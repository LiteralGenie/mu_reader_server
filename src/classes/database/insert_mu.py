import logging
import re
import sqlite3
import time


def s(text: str):
    if text is None: return None

    ret = text.replace("'", "''")
    ret = f"'{ret}'"
    ret = ret.strip()
    return ret

###

def insert_series(d: dict, op='IGNORE') -> str:
    raw = d['year'] or ''
    raw = re.sub(r'[;–.]', '-', raw)
    years = raw.split('-')
    if d['year'] is None or d['year'].strip() == '':
        years = ['NULL', 'NULL']
    elif re.search(r'n/a', d['year'], flags=re.IGNORECASE):
        years = ['NULL', 'NULL']
    elif len(years) == 2:
        years = [int(x) for x in years]
    elif len(years) == 1:
        years = [int(years[0]), 'NULL']
    elif len(years) == 3 and re.search(r'\d{4}-\d{1,2}-\d{1,2}', raw):
        logging.warning(f'Ignoring month + date in [{d["year"]}]')
        years = [int(years[0]), 'NULL']
    else:
        logging.warning(f'Unable to parse date from [{d["year"]}]')
        raise ValueError

    return f"""
        INSERT OR {op} INTO series VALUES (
            {d['series_id']},
            {s(d['title'])},
            {s(d['url'])},
            {s(d['description']) or "''"},
            {years[0]},
            {years[1]},
            {d['bayesian_rating'] or 'NULL'},
            {d['rating_votes']},
            {d['latest_chapter']},
            {d['forum_id']},
            {s(d['status']) or 'NULL'},
            {d['licensed']},
            {d['completed']},
            {d['last_updated']['timestamp']}
        )
    """

def insert_titles(d: dict, op='IGNORE') -> str:
    titles = [d['title']] + [x['title'] for x in d['associated']]
    values = [
        f"""(
            {d['series_id']}, {s(x)}
        )"""
        for x in titles
    ]

    return f"""
        INSERT OR {op} INTO titles VALUES {','.join(values)}
    """

def insert_images(d: dict, op='IGNORE') -> str:
    if d['image']['url']['original'] is None: return

    i = d['image']
    return f"""
        INSERT OR {op} INTO images VALUES (
            {d['series_id']},
            {s(i['url']['original'])},
            {s(i['url']['thumb'])},
            {i['height']},
            {i['width']}
        )
    """

def insert_types(d: dict, op='IGNORE') -> str:
    return f"""
        INSERT OR IGNORE INTO types (name) VALUES (
            {s(d['type']).lower()}
        )
    """

def insert_series_types(d: dict, op='IGNORE') -> str:
    return f"""
        INSERT OR {op} INTO series_types VALUES (
            {d['series_id']},
            (SELECT id from types WHERE name={s(d['type'].lower())})
        )
    """

def insert_genres(d: dict, op='IGNORE') -> str:
    if len(d['genres']) == 0: return

    genres = [x['genre'] for x in d['genres']]
    values = [
        f"""(
            {s(x).lower()}
        )"""
        for x in genres
    ]

    return f"""
        INSERT OR IGNORE INTO genres (name) VALUES {','.join(values)}
    """

def insert_series_genres(d: dict, op='IGNORE') -> str:
    if len(d['genres']) == 0: return

    genres = [x['genre'] for x in d['genres']]
    genres = [x.lower() for x in genres]
    values = [
        f"""(
            {d['series_id']},
            (SELECT id from genres WHERE name={s(x)})
        )"""
        for x in genres
    ]
    
    return f"""
        INSERT OR {op} INTO series_genres VALUES {','.join(values)}
    """

def insert_categories(d: dict, op='IGNORE') -> str:
    if len(d['categories']) == 0: return

    categories = [x['category'].lower() for x in d['categories']]

    values = [
        f"""(
            {s(x)}
        )"""
        for x in categories
    ]
    
    return f"""
        INSERT OR IGNORE INTO categories (name) VALUES {','.join(values)}
    """

def insert_series_categories(d: dict, op='IGNORE') -> str:
    if len(d['categories']) == 0: return

    categories = d['categories']

    values = [
        f"""(
            {d['series_id']},
            (SELECT id from categories WHERE name={s(x['category'].lower())}),
            {x['votes']},
            {x['votes_plus']},
            {x['votes_minus']},
            {x['added_by']}
        )"""
        for x in categories
    ]
    
    return f"""
        INSERT OR {op} INTO series_categories VALUES {','.join(values)}
    """

def insert_relations_types(d: dict, op='IGNORE') -> str:
    if len(d['related_series']) == 0: return

    relations = d['related_series']

    values = [
        f"""(
            {s(x['relation_type']).lower()}
        )"""
        for x in relations
    ]
    
    return f"""
        INSERT OR IGNORE INTO relations_types (name) VALUES {','.join(values)}
    """

def insert_series_relations(d: dict, op='IGNORE') -> str:
    if len(d['related_series']) == 0: return

    relations = d['related_series']
    id_pairs = [[d['series_id'], x['related_series_id']] for x in relations]
    id_pairs = [sorted(x) for x in id_pairs]
    
    values = [
        f"""(
            {id_pairs[i][0]},
            {id_pairs[i][1]},
            (SELECT id from relations_types WHERE name={s(x['relation_type'].lower())}),
            {x['triggered_by_relation_id']}
        )"""
        for i,x in enumerate(relations)
    ]
    
    return f"""
        INSERT OR {op} INTO series_relations VALUES {','.join(values)}
    """

def insert_authors(d: dict, op='IGNORE') -> list[str]:
    if len(d['authors']) == 0: return []

    authors_id = [x for x in d['authors'] if x['author_id']]
    values_id = [
        f"""(
            {x['author_id']},
            {s(x['name'])}
        )"""
        for x in authors_id
    ]
    query_id = f"INSERT OR {op} INTO authors VALUES {','.join(values_id)}"

    authors_no_id = [x for x in d['authors'] if x['author_id'] is None]
    values_no_id = [
        f"""(
            {s(x['name'])}
        )"""
        for x in authors_no_id
    ]
    query_no_id = f"INSERT OR IGNORE INTO authors (name) VALUES {','.join(values_no_id)}"
    
    ret = []
    if authors_id: ret.append(query_id)
    if authors_no_id: ret.append(query_no_id)
    return ret

def insert_authors_types(d: dict, op='IGNORE') -> str:
    if len(d['authors']) == 0: return

    authors = d['authors']

    values = [
        f"""(
            {s(x['type'].lower())}
        )"""
        for x in authors
    ]
    
    return f"""
        INSERT OR IGNORE INTO authors_types (name) VALUES {','.join(values)}
    """

def insert_series_authors(d: dict, op='IGNORE') -> str:
    if len(d['authors']) == 0: return
    
    authors = d['authors']

    values = []
    for x in authors:
        id = x['author_id'] or f"(SELECT id FROM authors WHERE name={s(x['name'])})"
        values.append(f"""(
            {d['series_id']},
            {id},
            (SELECT id from authors_types WHERE name={s(x['type'].lower())})
        )""")
    
    return f"""
        INSERT OR {op} INTO series_authors VALUES {','.join(values)}
    """

def insert_publishers(d: dict, op='IGNORE') -> str:
    grp = [x for x in d['publishers'] if x['publisher_id']]
    if len(grp) == 0: return

    no_ids = [x for x in d['publishers'] if x['publisher_id'] is None]
    if len(no_ids) > 0: logging.warning(f'Ignoring publishers with no id: {str(d)}')

    values = [
        f"""(
            {x['publisher_id']},
            {s(x['publisher_name'])}
        )"""
        for x in grp
    ]
    
    return f"""
        INSERT OR {op} INTO publishers VALUES {','.join(values)}
    """

def insert_publishers_types(d: dict, op='IGNORE') -> str:
    if len(d['publishers']) == 0: return

    grp = d['publishers']

    values = [
        f"""(
            {s(x['type'].lower())}
        )"""
        for x in grp
    ]
    
    return f"""
        INSERT OR {op} INTO publishers_types (name) VALUES {','.join(values)}
    """

def insert_series_publishers(d: dict, op='IGNORE') -> str:
    grp = [x for x in d['publishers'] if x['publisher_id']]
    if len(grp) == 0: return
    
    no_ids = [x for x in d['publishers'] if x['publisher_id'] is None]
    if len(no_ids) > 0: logging.warning(f'Ignoring series_publishers with no id: {str(d)}')

    values = [
        f"""(
            {d['series_id']},
            {x['publisher_id']},
            (SELECT id FROM publishers_types WHERE name={s(x['type'].lower())}),
            {s(x['notes']) or 'NULL'}
        )"""
        for x in grp
    ]
    
    return f"""
        INSERT OR {op} INTO series_publishers VALUES {','.join(values)}
    """

def insert_series_publications(d: dict, op='IGNORE') -> str:
    grp = d['publications']
    if len(grp) == 0: return

    values = [
        f"""(
            {d['series_id']},
            {x['publisher_id'] or 'NULL'},
            {s(x['publication_name'])}
        )"""
        for x in grp
    ]
    
    return f"""
        INSERT OR {op} INTO series_publications VALUES {','.join(values)}
    """

def insert_series_recommendations(d: dict, op='IGNORE') -> str:
    grp = d['recommendations']
    if len(grp) == 0: return

    values = [
        f"""(
            {d['series_id']},
            {x['series_id']},
            {x['weight']}
        )"""
        for x in grp
    ]
    
    return f"""
        INSERT OR {op} INTO series_recommendations VALUES {','.join(values)}
    """

def insert_series_category_recommendations(d: dict, op='IGNORE') -> str:
    grp = d['recommendations']
    if len(grp) == 0: return

    values = [
        f"""(
            {d['series_id']},
            {x['series_id']},
            {x['weight']}
        )"""
        for x in grp
    ]
    
    return f"""
        INSERT OR {op} INTO series_category_recommendations VALUES {','.join(values)}
    """

def insert_series_anime(d: dict, op='IGNORE') -> str:
    if d['anime']['start'] is None: return
    
    return f"""
        INSERT OR {op} INTO series_anime VALUES (
            {d['series_id']},
            {s(d['anime']['start'])},
            {s(d['anime']['end']) or 'NULL'}
        )
    """

def insert_series_rank(d: dict, op='IGNORE') -> str:    
    r = d['rank']

    return f"""
        INSERT OR {op} INTO series_rank VALUES (
            {d['series_id']},
            {r['position']['week'] or 'NULL'},
            {r['position']['month'] or 'NULL'},
            {r['position']['three_months'] or 'NULL'},
            {r['position']['six_months'] or 'NULL'},
            {r['position']['year'] or 'NULL'},
            {r['old_position']['week'] or 'NULL'},
            {r['old_position']['month'] or 'NULL'},
            {r['old_position']['three_months'] or 'NULL'},
            {r['old_position']['six_months'] or 'NULL'},
            {r['old_position']['year'] or 'NULL'},
            {r['lists']['reading'] or 'NULL'},
            {r['lists']['wish'] or 'NULL'},
            {r['lists']['complete'] or 'NULL'},
            {r['lists']['unfinished'] or 'NULL'},
            {r['lists']['custom'] or 'NULL'}
        )
    """

def insert_series_meta(d: dict, last_fetch: int, op='IGNORE') -> str:
    return f"""
        INSERT OR {op} INTO series_meta VALUES (
            {d['series_id']},
            {int(last_fetch)}
        )
    """

def get_series_query(d: dict, op='IGNORE') -> list[str]:
    ret = [
        insert_series(d, op=op),
        insert_titles(d, op=op),
        insert_images(d, op=op),
        insert_types(d, op=op),
        insert_series_types(d, op=op),
        insert_genres(d, op=op),
        insert_series_genres(d, op=op),
        insert_categories(d, op=op),
        insert_series_categories(d, op=op),
        insert_relations_types(d, op=op),
        insert_series_relations(d, op=op),
        *insert_authors(d, op=op),
        insert_authors_types(d, op=op),
        insert_series_authors(d, op=op),
        insert_publishers(d, op=op),
        insert_publishers_types(d, op=op),
        insert_series_publishers(d, op=op),
        insert_series_publications(d, op=op),
        insert_series_recommendations(d, op=op),
        insert_series_category_recommendations(d, op=op),
        insert_series_anime(d, op=op),
        insert_series_rank(d, op=op),
        insert_series_meta(d, int(time.time()), op=op)
    ]
    ret = [x for x in ret if x is not None]
    return ret

def insert(d: dict, cursor: sqlite3.Cursor, op='IGNORE'):
    qs = get_series_query(d, op=op)
    for q in qs:
        cursor.execute(q)
