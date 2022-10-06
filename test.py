inputp = 0
out = 0

while out < 1095:
    inputp += 1
    out += len(str(inputp))

print(out)
