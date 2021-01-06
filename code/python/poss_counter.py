from typing import Dict, List


def counts(domain_size: int, unique_name_assumption: bool = False) -> Dict[int, List[int]]:
    # alpha = fr(a,b)
    # beta  = fr(a,b) AND fr(b,c)
    out_dict = {}
    for size in range(domain_size):
        print(size)
    return out_dict
