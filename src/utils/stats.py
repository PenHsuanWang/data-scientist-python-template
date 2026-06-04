def calculate_mean(data: list[float | int]) -> float:
    """
    Calculate the arithmetic mean of a list of numbers.

    :param data: A list of numerical values.
    :return: The mean value.
    :raises ValueError: If the data list is empty.
    """
    if not data:
        raise ValueError("Cannot calculate mean of an empty list")
    return sum(data) / len(data)
