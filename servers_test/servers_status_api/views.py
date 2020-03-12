from django.shortcuts import render
import requests
import re
import subprocess
from bs4 import BeautifulSoup
from django.http import JsonResponse
from .models import SeversHistory
from django.utils import timezone
import json

# Create your views here.

# custom ssl grade for solve scale in test
SSL_GRADE_LEVEL = {
    "A+": 0,
    "A": 1,
    "B+": 2,
    "B": 3,
    "C+": 4,
    "C": 5
}


def index(request):
    return render(request, 'index.html', {})


def status_response(request, url):
    # Empty list for a new dictionary how contains info about servers
    servers = []

    # Get the dictionary and values who return the consult
    get_result = requests.get(f'https://api.ssllabs.com/api/v3/analyze?host={url}')
    get_result_dic = get_result.json()
    # This variable fake response for testing, because sometimes the server block
    """get_result_dic = json.loads(
    '{"host":"truora.com","port":443,"protocol":"http","isPublic":false,"status":"IN_PROGRESS","startTime":1583966769611,"engineVersion":"2.1.0","criteriaVersion":"2009q","endpoints":[{"ipAddress":"34.193.204.92","serverName":"redirect1.proxy-ssl.webflow.com","statusMessage":"Ready","grade":"C","gradeTrustIgnored":"A","hasWarnings":false,"isExceptional":false,"progress":100,"duration":90668,"delegation":1},{"ipAddress":"34.193.69.252","grade":"A+","serverName":"redirect2.proxy-ssl.webflow.com","statusMessage":"In progress","statusDetails":"TESTING_SUITES","statusDetailsMessage":"Determining available cipher suites","progress":62,"eta":11,"delegation":1}]}')"""

    # Loop extract data from dictionary and update server list
    for i in get_result_dic['endpoints']:
        servers.append({'address': i.get('ipAddress'), 'ssl_grade': i.get('grade')})
    # This loop contains a function how get all servers ip info and extract data
    ssl_grade = None
    for s in servers:
        ip = (s['address'])

    if not ssl_grade:
        ssl_grade = SSL_GRADE_LEVEL.get(s['ssl_grade'])
    else:
        if SSL_GRADE_LEVEL.get(s['ssl_grade']) > ssl_grade:
            ssl_grade = SSL_GRADE_LEVEL.get(s['ssl_grade'])

    # This function uses regex to extract data from text and update servers dictionary

    response_whois_ip = str(subprocess.run(['whois', ip], stdout=subprocess.PIPE))
    organization_regex = re.compile(r"OrgName:[\s]*([\w\s\n]+)")
    country_regex = re.compile(r"Country:[\s]*([\w\s\n]+)")
    find = organization_regex.search(str(response_whois_ip))
    find_2 = country_regex.search(str(response_whois_ip))
    try:
        s.update({
            'owner': find.group(1),
            'country': find_2.group(1)
        })
    except AttributeError:
        pass

    # Variable how contains all object with list of dic called servers

    for k, v in SSL_GRADE_LEVEL.items():
        if v == ssl_grade:
            ssl_grade = k

    final_response = {'servers': servers, 'ssl_grade': ssl_grade}

    # This part get al data for the last server status
    url_response_status = requests.get(f'https://{url}')

    if url_response_status.status_code == 200:
        final_response.update({'is_down': False})
    else:
        final_response.update({'is_down': True})

    # Using BeautifulSoup for get title and logo from html content

    html_content = url_response_status.text

    soup = BeautifulSoup(html_content, 'lxml')
    if soup.title.parent.name == 'head':
        final_response.update({'title': soup.title.string})

    # this value rel icon only works with truora.com, however other pages pass
    try:
        image_find = soup.find("link", rel='icon')
        final_response.update({'logo': image_find.get('href')})
    except AttributeError:
        pass

    # Compare ssl grade change in ssl grade in an hour difference
    if SeversHistory.objects.filter(domain_name=url).count() == 0:
        # When database don't have info show null or none
        final_response.update({'previous_ssl_grade': None})
        # Create the register in DB
        SeversHistory.objects.create(domain_name=str(url), server_information=final_response)
    else:
        # Order exist objects by date if exist only
        last_search = SeversHistory.objects.filter(domain_name=url).order_by('-consultation_date')[0]
        now = timezone.now()
        # Compare if changes in a hour with ssl grade
        if (now - last_search.consultation_date).total_seconds() > 60 * 60:
            # You can convert for seconds removing *60
            last_final_response = last_search.server_information
            final_response.update({'previous_ssl_grade': last_final_response['ssl_grade']})
            # Save the last response for compare whit the new one in one hour or more
            SeversHistory.objects.create(domain_name=str(url), server_information=final_response)

        else:
            # Return this value if user try to get response less than an hour
            final_response.update({'previous_ssl_grade': None})

    """TODO i don't finish the server compare respect an hour a go """

    return JsonResponse(final_response)


# This function return the second endpoint
def history_responses(request):
    history = {"items": []}
    for i in SeversHistory.objects.all().values('domain_name').distinct():
        sh = SeversHistory.objects.filter(domain_name=i["domain_name"]).order_by('-consultation_date')[0]
        history["items"].append({i["domain_name"]: sh.server_information})

    return JsonResponse(history)
