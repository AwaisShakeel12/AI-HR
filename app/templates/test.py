import os
def candies(n, arr):
    # Write your code here

    if __name__ == '__main__':
        fptr = open(os.environ['OUTPUT_PATH'], 'w')

    n = int(input().strip())

    arr = []

    for _ in range(n):
        arr_item = int(input().strip())
        arr.append(arr_item)

    result = candies(n, arr)
    print(result)

    fptr.write(str(result) + '\n')

    fptr.close()