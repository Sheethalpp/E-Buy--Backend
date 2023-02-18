from django.core.exceptions import ValidationError


def validate_product_img_size(file):
    max_size_kb = 1024
    if file.size > max_size_kb * 1024:
        raise ValidationError(
            f'file size cannot be larger than {max_size_kb}KB')
