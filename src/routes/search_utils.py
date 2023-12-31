import logging
logger = logging.getLogger(__name__)

from pydantic import BaseModel
from typing import List, Any

class SearchResult(BaseModel):
    total_results_number: int
    page_number: int = 0
    page_size: int | None = None
    results: List[Any]

def page_result_formater(results: list, page_size: int | None, page_number: int, max_page_size: int = 1000) -> SearchResult:
    if not page_size:
        page_size=max_page_size
    start_index = page_size*page_number
    end_index = page_size*(page_number+1)
    results_number = len(results)-1
    if page_size and len(results) > page_size:
        end_index = results_number if results_number < end_index else end_index
        return SearchResult(total_results_number=len(results), page_size=page_size, page_number=page_number, results=results[start_index:end_index])
    return SearchResult(total_results_number=len(results), page_size=page_size, page_number=page_number, results=results)

def extract_search_params_from_request(query_params: list, black_list_values: list):
    query_params_dict = {}
    for search_condition in query_params:
        current_key=search_condition[0]
        if search_condition[0] in black_list_values:
            continue
        if not current_key in query_params_dict:
            query_params_dict[current_key] = []
        query_params_dict[current_key].append(search_condition[1])
    return query_params_dict