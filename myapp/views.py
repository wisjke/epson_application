from django.shortcuts import render, redirect, get_object_or_404
from .forms import UploadForm
from .models import Upload
from .tools import SalersReader, MerchReader
from collections import Counter

def slicer(elem):
    return int(elem.split(' ')[1])

def upload_files(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save()
            return redirect('process_files', pk=upload.pk)
        else:
            print(form.errors)
    else:
        form = UploadForm()
    return render(request, 'upload.html', {'form': form})

def process_files(request, pk):
    upload = get_object_or_404(Upload, pk=pk)
    salers_path = upload.salers_file.path
    merch_path = upload.merch_file.path

    salers = {}
    merchs = {}
    error_message = ""

    try:
        salersReader = SalersReader(salers_path)
        salers = salersReader.read()
    except Exception as e:
        error_message += f"Error reading 'salers.csv': {e}\n"

    try:
        merchReader = MerchReader(merch_path)
        merchs = merchReader.read()
    except Exception as e:
        error_message += f"Error reading 'Merch.xlsx': {e}\n"

    city_results = {}
    for err, cities in merchs.items():
        for city, phones in cities.items():
            task_phone_map = {}
            for phone in phones:
                if phone in salers:
                    tasks = salers[phone]
                    for task in tasks:
                        task_number = slicer(task)
                        if task_number not in task_phone_map:
                            task_phone_map[task_number] = {'count': 0, 'phones': []}
                        task_phone_map[task_number]['count'] += 1
                        task_phone_map[task_number]['phones'].append(phone)
            sorted_tasks = sorted(task_phone_map.items())
            result = {'error': err, 'tasks': sorted_tasks}

            if city not in city_results:
                city_results[city] = [result]
            else:
                city_results[city].append(result)

    upload.salers_file.delete()
    upload.merch_file.delete()
    upload.delete()

    return render(request, 'results.html', {'city_results': city_results, 'error_message': error_message})