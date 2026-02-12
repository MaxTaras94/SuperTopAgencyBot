link = "https://drive.google.com/drive/u/2/folders/14S6NUrNnAqDiOQ__JotF8UdDYwVHoHFn"
print(link.split('/')[-1])
SELECTING_ACTION, ADDING_MEMBER, ADDING_SELF, DESCRIBING_SELF = map(chr, range(4))


from math import ceil

def chunk(lst, size):
  return list(
    map(lambda x: lst[x * size:x * size + size],
      list(range(0, ceil(len(lst) / size)))))

chunk([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 4)