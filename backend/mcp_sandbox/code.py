def bubble_sort(arr):
    """
    Sorts an array using the bubble sort algorithm.
    Use cases:
    1. Educational purposes to demonstrate sorting algorithms.
    2. Small datasets where performance is not critical.
    3. Situations where simplicity of implementation is more important than efficiency.
    """
    n = len(arr)
    for i in range(n):
        for j in range(0, n-i-1):
            if arr[j] > arr[j+1]:
                arr[j], arr[j+1] = arr[j+1], arr[j]
    return arr

# Example usage:
if __name__ == '__main__':
    sample_array = [64, 34, 25, 12, 22, 11, 90]
    sorted_array = bubble_sort(sample_array)
    print("Sorted array is:", sorted_array)
