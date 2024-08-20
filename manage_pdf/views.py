from django.shortcuts import render, redirect
from django.core.files.storage import FileSystemStorage
from django.urls import reverse
from django.http import JsonResponse, FileResponse, Http404
import os
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
import uuid
from datetime import datetime
import time
import json
from wsgiref.util import FileWrapper
import tempfile
import shutil
import logging

# Create your views here.

def index(request):
    return render(request, 'index.html')

def upload_pdf(request):  # Corrected function name
    if request.method == 'POST' and request.FILES.get('pdf_file'):
        file = request.FILES['pdf_file']
        fs = FileSystemStorage()
        filename = fs.save(file.name, file)
        file_url = fs.url(filename)

        file_path = fs.path(filename)
        request.session['file_path'] = file_path

        return render(request, 'display_pdf.html', {'file_url': file_url})
    
    return render(request, 'upload_pdf.html')

def split_pdf(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        pgno = data.get('pgno')

        file_path = request.session.get('file_path')

        if file_path and os.path.exists(file_path) and pgno:
            pdf_reader = PdfReader(file_path)
            pdf_writer = PdfWriter()
            x1 = len(pdf_reader.pages)

            for page_num in pgno:
                if page_num <= x1 :
                    pdf_writer.add_page(pdf_reader.pages[page_num-1])
                
                else:
                    print(f"Page number {page_num} is out of range.")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"output_{timestamp}_{uuid.uuid4().hex}.pdf"
            output_pdf_path = os.path.join(os.getcwd(), unique_filename)

            with open(output_pdf_path, 'wb') as output_pdf:
                pdf_writer.write(output_pdf)

            request.session['output_pdf_path'] = output_pdf_path

            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'File not found'}, status=400)
    else:
        return JsonResponse({'status': 'invalid method'}, status=400)

def pdf_download(request):
    output_pdf_path = request.session.get("output_pdf_path")
    merged_pdf_path = request.session.get("merged_pdf_path")

    if output_pdf_path and os.path.exists(output_pdf_path):
        file_name = os.path.basename(output_pdf_path)
        download_url = request.build_absolute_uri(reverse('manage_pdf:download_file', args=[file_name]))
        # Optionally clear the session here if you want to delete the file after download
        del request.session['output_pdf_path']
        return render(request, 'pdf_download.html', {'download_url': download_url})
    
    elif merged_pdf_path and os.path.exists(merged_pdf_path):
        file_name = os.path.basename(merged_pdf_path)
        download_url = request.build_absolute_uri(reverse('manage_pdf:download_file', args=[file_name]))
        # Optionally clear the session here if you want to delete the file after download
        del request.session['merged_pdf_path']
        return render(request, 'pdf_download.html', {'download_url': download_url})
    
    else:
        return render(request, 'pdf_download.html', {'error': 'File not found'})

def download_file(request, filename):
    file_path = os.path.join(os.getcwd(), filename)
    print(f"Attempting to download file: {file_path}")

    if os.path.exists(file_path):
        try:
            # Open the file and keep it open while sending it in the response
            f = open(file_path, 'rb')
            response = FileResponse(f, as_attachment=True, filename=filename)

            # Once the response is fully sent, delete the file
            def file_closure(file_obj, path):
                file_obj.close()  # Close the file object
                try:
                    os.remove(path)  # Attempt to delete the file
                    print(f"File {path} successfully deleted after download.")
                except Exception as e:
                    print(f"Failed to delete file {path}: {str(e)}")
                    logging.error(f"Failed to delete file {path}: {str(e)}")

            # Attach the cleanup action to the response close method
            response['Close-File-Action'] = lambda: file_closure(f, file_path)

            return response
        except Exception as e:
            print(f"Error serving file: {str(e)}")
            raise Http404("File could not be served.")
    else:
        raise Http404("File not found")

def upload_pdfs(request):
    if request.method == 'POST' and request.FILES.getlist('pdfs'):
        pdf_files = request.FILES.getlist('pdfs')
        fs = FileSystemStorage()
        
        file_paths = []

        for pdf in pdf_files:
            filename = fs.save(pdf.name, pdf)
            file_path = fs.path(filename)
            file_paths.append(file_path)

        # Store file paths in session
        request.session['file_paths'] = file_paths    

        # Redirect to the merge function after uploading files
        return redirect('manage_pdf:merge_pdf')

    return render(request, 'upload_pdfs.html')

def merge_pdf(request):
    # Get the list of file paths from the session
    file_paths = request.session.get("file_paths")
    
    if file_paths:
        try:
            # If there's an old merged PDF in the session, delete it
            old_merged_pdf_path = request.session.get("merged_pdf_path")
            if old_merged_pdf_path and os.path.exists(old_merged_pdf_path):
                os.remove(old_merged_pdf_path)
                del request.session['merged_pdf_path']

            merger = PdfMerger()

            # Merge the PDFs
            for file_path in file_paths:
                if os.path.exists(file_path):
                    merger.append(file_path)
                else:
                    print(f"File not found: {file_path}")

            # Create a unique filename for the merged PDF
            timestamp = int(time.time())
            unique_filename = f'merged_{timestamp}.pdf'
            output_path = os.path.join(os.getcwd(), unique_filename)

            # Save the merged PDF
            with open(output_path, 'wb') as output_file:
                merger.write(output_file)
            
            merger.close()

            # Store the new merged file path in the session
            request.session['merged_pdf_path'] = output_path

            # Clear the session file paths after merging
            del request.session['file_paths']

            # Return JSON response with download URL
            download_url = reverse('manage_pdf:pdf_download')
            return JsonResponse({'status': 'success', 'download_url': download_url})

        except Exception as e:
            print(f"Error during merge: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)})

    return JsonResponse({'status': 'error', 'message': 'No files to merge'})
