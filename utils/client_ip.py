def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_list = x_forwarded_for.split(',')
    
        return ip_list[0].strip()
        
    return request.META.get('REMOTE_ADDR')