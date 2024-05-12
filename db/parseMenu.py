import json

with open('temp.txt') as file:
    arr = [line.strip() for line in file.readlines()]
    arr = [line for line in arr if len(line)]

orders = {'products': {}}
ni = 0
count = 0
for i, line in enumerate(arr):
    if ':' in line:
        ni = i
        break
    jnd = -1
    price = 0
    for j, otr in enumerate(line.split()):
        try:
            price = int(otr)
            jnd = j
            break
        except:
            continue
    name = ' '.join(line.split()[:jnd])
    orders['products'][str(count)] = {
        'name': name,
        'price': price,
        'categoryId': None,
        'active': True
    }
    count += 1

catId = -1
for i, line in enumerate(arr[ni:], start=ni):
    if ':' in line:
        nameCat = line[:line.index(':')]
        catId += 1
    else:
        nameProd = ' '.join(line.split())
        for key, info in orders['products'].items():
            if info['name'] == nameProd:
                orders['products'][key]['categoryId'] = str(catId)
                break

with open('parse.json', 'w', encoding='utf-8') as file:
    json.dump(orders, file, indent=4, ensure_ascii=False)

print(orders)