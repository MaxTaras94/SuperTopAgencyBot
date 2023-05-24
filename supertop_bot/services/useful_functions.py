from math import ceil
from typing import List


def get_id_from_link(link)-> str:
    return link.split('/')[-1]

def generate_links_for_sharing(links_id: List[str]) -> List[str]:
    links_for_sharing = []
    for link in links_id:
        links_for_sharing.append(f'https://docs.google.com/uc?export=download&id={link}')
    return links_for_sharing
    

def chunk(lst:list, size:int) -> list[list]:
  '''Функция на вход принимает длинный список и некое целое число n. В рез-те выполнения возвращает список списков, в каждом из которых будет n-е кол-во элементов'''
  return list(
    map(lambda x: lst[x * size:x * size + size],
      list(range(0, ceil(len(lst) / size)))))