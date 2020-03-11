from django.shortcuts import render
import requests
import re
import subprocess
from bs4 import BeautifulSoup
from django.http import JsonResponse
from .models import SeversHistory
from django.utils import timezone


# Create your views here.

def index(request):
    return render(request, 'index.html', {})


def status_response(request, url):
    # Empty list for a new dictionary how contains info about servers
    servers = []

    # Get the dictionary and values who return the consult
    get_result = requests.get(f'https://api.ssllabs.com/api/v3/analyze?host={url}')
    get_result_dic = get_result.json()

    # Loop extract data from dictionary and update server list
    for i in get_result_dic['endpoints']:
        servers.append({'address': i['ipAddress'], 'ssl_grade': i['grade']})
    # This loop contains a function how get all servers ip info and extract data
    for s in servers:
        ip = (s['address'])

        # This function uses regex to extract data from text and update servers dictionary
        def whois_ip(ip):
            response_whois_ip = subprocess.run(['whois', ip], stdout=subprocess.PIPE)
            info_response = str(response_whois_ip)
            response_whois_ip = info_response
            organization_regex = re.compile(r"OrgName:[\s]*([\w\s\n]+)")
            country_regex = re.compile(r"Country:[\s]*([\w\s\n]+)")
            find = organization_regex.search(str(response_whois_ip))
            find_2 = country_regex.search(str(response_whois_ip))
            return {'owner': find.group(1), 'country': find_2.group(1)}

    # Variable how contains all object with list of dic called servers
    final_response = {'servers': servers}

    # This part get al data for the last server status
    url_response_status = requests.get(url)

    if url_response_status.status_code == 200:
        final_response.update({'is_down': False})
    else:
        final_response.update({'is_down': True})

    # Using BeautifulSoup for get title and logo from html content

    html_content = url_response_status.text

    soup = BeautifulSoup(html_content, 'lxml')
    if soup.title.parent.name == 'head':
        final_response.update({'title': soup.title.string})
    try:
        image_find = soup.find("link", rel='icon')
        final_response.update({'logo': image_find.get('href')})
    except AttributeError:
        pass

    save_final_response = SeversHistory.objects.create(domain_name=str(url),
                                                       server_information=final_response)
    save_final_response.save()

    items = []
    for lr in SeversHistory.objects.all():
        domain = lr.domain_name
        info = lr.server_information
        items.append({'domain_name': domain, 'info': info})
        return JsonResponse(items, safe=False)

    return JsonResponse(final_response)
