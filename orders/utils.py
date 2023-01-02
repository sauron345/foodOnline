from datetime import datetime
import json


def generate_order_number(pk):
    current_time = datetime.now().strftime('%Y%m%d%H%M%S') + str(pk)  # 20221213162757 + pk
    return current_time


def order_total_by_vendor(order, vendor_id):
    total_data = json.loads(order.total_data)
    data = total_data.get(str(vendor_id))
    subtotal = 0
    tax = 0
    tax_dict = {}

    for k, v in data.items():
        tax_dict.update(v)
        subtotal += float(k)
        for i in v:
            for j in v[i]:
                v[i][j] = str(v[i][j])
        v = str(v)
        v = v.replace("'", '"')
        v = json.loads(v)

        for i in v:
            for j in v[i]:
                tax += float(v[i][j])

    grand_total = float(subtotal) + float(tax)

    context = {
        'subtotal': subtotal,
        'tax_dict': tax_dict,
        'grand_total': grand_total,
    }

    return context
