import time
from celery import shared_task
from notifications.utils import send_task_progress


@shared_task(bind=True)
def run_product_analysis(self, product_url):
    task_id = self.request.id

    # Stage 1: Initialization
    send_task_progress(task_id, step='INIT', progress_percent=10, message='Initializing scraping engine...')
    time.sleep(1)

    # Stage 2: Scraping reviews
    send_task_progress(task_id, step='SCRAPING', progress_percent=35, message=f'Navigating and extracting reviews from {product_url}...')
    time.sleep(2)

    # Stage 3: Data Analysis
    send_task_progress(task_id, step='ANALYZING', progress_percent=70, message='Analyzing review velocity and semantic patterns...')
    time.sleep(2)

    # Stage 4: Scoring
    send_task_progress(task_id, step='SCORING', progress_percent=90, message='Calculating True Trust Score and dark patterns...')
    time.sleep(1)

    # Stage 5: Completion
    send_task_progress(task_id, step='COMPLETED', progress_percent=100, message='Analysis complete.')

    return {'status': 'success', 'url': product_url}