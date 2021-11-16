lines = []
f = open("graph/as19990829.txt", "r")
ind = 1
while 1:
    line = f.readline()
    if not line:
        break
    # print(line)
    if line[0] == '#':
        line = line[:-1] + "\t"
        lines.append(line)
    else:
        n1, n2 = [int(x) for x in line.strip().split()]
        # print(n1, n2)
        lines.append(str(n1) + "   " + str(n2) + "   " + str(ind))
        ind += 1

# print(lines)
f = open("graph/weighted.txt", "w+")

for line in lines:
    # print(line)
    print(line, file=f)
f.close()
