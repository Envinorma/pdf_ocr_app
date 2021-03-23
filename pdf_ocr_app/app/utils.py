def generate_id(filename: str, suffix: str) -> str:
    prefix = filename.split('/')[-1].replace('.py', '').replace('_', '-')
    return prefix + '-' + suffix
