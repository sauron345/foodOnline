from datetime import datetime


def generate_order_number(pk):
    current_time = datetime.now().strftime('%Y%m%d%H%M%S') + str(pk)  # 20221213162757 + pk
    return current_time
