import aiohttp
import asyncio
import re
from bs4 import BeautifulSoup
import os
from tqdm.asyncio import tqdm
from PIL import Image
from fpdf import FPDF
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import imghdr
import aiohttp
import asyncio
from PIL import Image
from io import BytesIO
import os,sys
from tqdm.asyncio import tqdm_asyncio
from pathlib import Path
import argparse
import warnings
import signal

def die(message):
    red = "\033[31m"
    reset = "\033[0m"
    print(f"[{red}warning{reset}] {message}")

def info(message):
    green = "\033[32m"
    r = "\033[0m"
    print(f"[{green}INFO{r}] {message}")

def handle_interrupt(signum, frame):
    print("")
    info("Program interrupted. Exiting gracefully.")
    sys.exit(0)  # Exit the program gracefully

signal.signal(signal.SIGINT, handle_interrupt)

async def get_chapters(post_id,referer='https://manytoon.org/comic/queen-bee-manhwa-hentai-003-mnt0017/'):
    # Define the URL
    url = "https://manytoon.org/wp-admin/admin-ajax.php"
    
    # Define the payload
    payload = {
        'post_id': post_id,
        'action': 'ajax_chap'
    }

    # Define headers
    headers = {
        'Authority': 'manytoon.org',
        'Accept': 'text/html, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Referer': referer,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=payload, headers=headers) as response:
            response_text = await response.text()
            return response.status, response_text

async def fetch_search_results(session, search_term):
    url = f"https://manytoon.org/?s={search_term}&post_type=wp-manga"
    async with session.get(url) as response:
        if response.status == 200:
            return await response.text()
        else:
            return None

def cleanup(name):
    # Check if it starts with "NEW" and ends with "end"
    if name.startswith("NEW"):
        if name[3] != " ":  # No space after "NEW"
            name.replace("NEW","")
            name_ = name.replace("NEW","")
            return name_
    if name.startswith("end"):
         if name[3] != " ":  # No space after "NEW"
            name.replace("end","")
            name_ = name.replace("end","")
            return name_
    return name  # Return the original name if conditions aren't met

def manga_data(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    manga_data = []

    # Locate the content listing
    manga_items = soup.find_all('div', class_='page-item-detail manga')

    for item in manga_items:
        title_element = item.find('h3', class_='h5')
        title = title_element.get_text(strip=True)
        link = title_element.find('a')['href']

        img_element = item.find('img')
        img_url = img_element['src']

        rating_element = item.find('div', class_='rate-item')
        rating = rating_element.find('div')['style'].replace('width: ', '').replace('%', '') if rating_element else 'No Rating'

        chapter_item = item.find('div', class_='list-chapter')
        latest_chapter_element = chapter_item.find('span', class_='chapter font-meta')
        latest_chapter_title = latest_chapter_element.get_text(strip=True) if latest_chapter_element else 'No Chapter'
        latest_chapter_link = latest_chapter_element.find('a')['href'] if latest_chapter_element else '#'

        post_date_element = chapter_item.find('span', class_='post-on font-meta')
        post_date = post_date_element.get_text(strip=True) if post_date_element else 'Unknown Date'

        # Check for ongoing badge
        ongoing_badge = title_element.find('span', class_='manga-title-badges')
        ongoing = ongoing_badge is not None and 'Ongoing' in ongoing_badge.text

        if ongoing and "Ongoing" in title:
           title = title.replace("Ongoing", "")
        name = cleanup(title)

        manga_info = {
            'title': name,
            'link': link,
            'image_url': img_url,
            'rating': rating,
            'latest_chapter': {
                'title': latest_chapter_title,
                'link': latest_chapter_link,
                'post_date': post_date,
            },
            'ongoing': ongoing
        }

        manga_data.append(manga_info)

    return manga_data


async def get_post_id(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
            soup = BeautifulSoup(html_content, 'html.parser')
            script_tag = soup.find('script', string=lambda x: x and 'comicObj' in x)
            
            if script_tag:
                script_content = script_tag.string
                post_id = script_content.split("post_id: '")[1].split("'")[0]
                return post_id
    return None

def extract_chapters(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    chapters = soup.find_all('li', class_='wp-manga-chapter')

    chapter_data = {
        'total_chapters': len(chapters),  # Total number of chapters
        'chapters': {}
    }

    for chapter in chapters:
        title = chapter.find('a').text.strip()
        chapter_number = float(title.split()[-1]) if '.' in title.split()[-1] else int(title.split()[-1])
#        chapter_number = init(title.split()[-1])  # Extract the number from the title
        link = chapter.find('a')['href']
        release_date = chapter.find('span', class_='chapter-release-date').text.strip()

        chapter_data['chapters'][chapter_number] = link

        """
        chapter_data['chapters'].append({
            'chapter': chapter_number,
            'link': link,
            'release_date': release_date
        })
        """
    return chapter_data

async def extract_images_from_chapter(url):
    async with aiohttp.ClientSession() as session:                        
       async with session.get(url) as response:
            html_content = await response.text()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all the img tags inside the div with class "reading-content"
    images = soup.find('div', class_='reading-content').find_all('img', class_='wp-manga-chapter-img')

    #image_data.sort(key=lambda x: int(re.search(r'/(\d+)(?:[_\.-][a-zA-Z]+)?\.[a-zA-Z]+$', x).group(1)) if re.search(r'/(\d+)(?:[_\.-][a-zA-Z]+)?\.[a-zA-Z]+$', x) else float('inf'))
    image_data = []

    # Loop through the images and extract src
    for img in images:
        image_src = img.get('src')
        if image_src:
            image_data.append(image_src)

    # Sort the image_data by the numeric part of the image file name, handling different formats
    #image_data.sort(key=lambda x: int(re.search(r'/(\d+)\.[a-zA-Z]+$', x).group(1)))
    #import re
    image_data.sort(key=lambda x: int(re.search(r'/(\d+)\.[a-zA-Z]+$', x).group(1)) if re.search(r'/(\d+)\.[a-zA-Z]+$', x) else float('inf'))
    result = {'urls': image_data}

    return result

async def download_image(session, url, progress_bar):
    retries = 5  # Number of retries
    for attempt in range(retries):
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    progress_bar.update(1)  # Update the progress bar on each successful download
                    return Image.open(BytesIO(image_data))
                else:
                    print(f"Failed to download {url}, status code: {response.status}")
                    progress_bar.update(1)  # Even if it fails, update the progress bar
                    return None
        except Exception as e:
            print(f"Error downloading {url} on attempt {attempt + 1}: {e}")
            #progress_bar.update(1)  # Update the progress bar in case of errors
            
            # If the last attempt fails, return None
            if attempt == retries - 1:
                sys.exit()
                return None
# Main async function to manage downloading images with a progress bar
async def download_images(image_urls):
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        # Initialize the progress bar with the total number of images
        with tqdm_asyncio(total=len(image_urls), desc="Downloading images",leave=False,unit="MB",unit_scale=1) as progress_bar:
            for url in image_urls:
                tasks.append(download_image(session, url, progress_bar))
            
            # Wait for all downloads to finish
            images = await asyncio.gather(*tasks)
            
            # Filter out any None values (failed downloads)
            images = [img for img in images if img is not None]
            
            return images


# Function to save images directly as a PDF
def save_images_as_pdf(images, output_file):
    if os.path.exists(output_file):
        print(f"PDF '{output_file}' already exists.")
        return
    if images:
        # Convert images to RGB with a progress bar
        pdf_images = []
        for img in tqdm(images, desc="Converting images", unit="image",leave=False):
            pdf_images.append(img.convert("RGB"))
        
        # Save the images as a single PDF file with progress indication
        info(f"Saving PDF as {output_file}...\n")
        with tqdm(total=len(pdf_images), desc="Saving PDF", unit="image",leave=False) as pbar:
            pdf_images[0].save(output_file, save_all=True, append_images=pdf_images[1:], resolution=100.0)
            pbar.update(len(pdf_images))
    else:
        print("No images to save.")


async def download_full(url,ch,path):
      ch_name = f"Chapter {ch}"
      pdf_path = Path(path) / f"{ch_name}.pdf"
      #data = await extract_images_from_chapter(url)
      if os.path.exists(pdf_path):
       # print(f"PDF '{pdf_path}' already exists.")
         return 
      else:
        data = await extract_images_from_chapter(url)
        info(f"Downloading Chapter {ch}")
        images = await download_images(data['urls'])
        info(f"Converting Into PDF: Chapter {ch}.pdf")
      pdf_path = Path(path) / f"{ch_name}.pdf"
      if os.path.exists(pdf_path):
        #print(f"PDF '{pdf_path}' already exists.")
         return
      else:
        save_images_as_pdf(images,pdf_path)
      #print(data)
        pass

async def download_chapters(chapter_dict, start_chapter, end_chapter,path):
    # Ensure that the user inputs a valid range
    """
    if start_chapter < 1 or end_chapter > max(chapter_dict['chapters'].keys()) or start_chapter > end_chapter:
        print("Invalid chapter range.")
        return
    """
    if start_chapter < 1 or start_chapter > max(chapter_dict['chapters'].keys()):
       print("Invalid chapter range.")
       return
    # Sort chapters in ascending order and select the required range
    sorted_chapters = dict(sorted(chapter_dict['chapters'].items()))
    selected_chapters = {k: v for k, v in sorted_chapters.items() if start_chapter <= k <= end_chapter}

    # Pass the chapter URLs to the download function in ascending order
    info("Download Started...")
    print("")
    for chapter, url in selected_chapters.items():
        #print(f"Downloading Chapter {chapter}")
        await download_full(url,chapter,path)

from pathlib import Path

def create_folder(base_path: str, folder_name: str) -> Path:
    # Create a Path object for the base path
    base = Path(base_path)
    
    # Create the full path for the new folder
    new_folder_path = base / folder_name
    
    # Check if the folder already exists
    if new_folder_path.exists():
        print(f"Folder '{new_folder_path}' already exists.")
        return new_folder_path  # Return the existing path
    else:
        # Create the new folder
        new_folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Folder '{new_folder_path}' created successfully.")
        return new_folder_path  # Return the newly created path

async def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Search and download manga chapters.")
    
    parser.add_argument(
        "search_term", type=str, help="Search term to find manga"
    )
    parser.add_argument(
        "--chapters", nargs=2, type=int, metavar=('start', 'end'),
        default=(1, 10), help="Chapter range to download (start end)"
    )
    parser.add_argument(
        "--path", type=str, default=os.getcwd(), 
        help="Directory where the chapters will be downloaded (default: current directory)"
    )
    parser.add_argument(
        "--input-pos", type=int, default=None,
        help="Position of the manga in the list to select automatically (1-based index)"
    )

    args = parser.parse_args()

    async with aiohttp.ClientSession() as session:
        info(f"Searching Manga: {args.search_term}")
        html_content = await fetch_search_results(session, args.search_term)

        if html_content:
            manga_details = manga_data(html_content)
            if manga_details:
                if args.input_pos is not None:
                    # Automatically select based on --input-pos
                    if 1 <= args.input_pos <= len(manga_details):
                        selected_manga = manga_details[args.input_pos - 1]
                        selected_link = selected_manga['link']
                    else:
                        print("Invalid --input-pos value. Out of range.")
                        return
                else:
                    # Manual selection if --input-pos is not provided
                    while True:
                        print("\nSelect a manga from the list below:")
                        for idx, manga in enumerate(manga_details, 1):
                            print(f"{idx}. {manga['title']} (Latest chapter: {manga['latest_chapter']['title']})")

                        try:
                            selection = int(input("\nEnter the number of the manga you want to select (or 0 to cancel): "))

                            if selection == 0:
                                print("Cancelled.")
                                return

                            if 1 <= selection <= len(manga_details):
                                selected_manga = manga_details[selection - 1]
                                selected_link = selected_manga['link']
                                break
                            else:
                                print("Invalid selection. Please try again.")
                        except ValueError:
                            print("Invalid input. Please enter a valid number.")
            else:
                print("No manga found.")
                return
        else:
            print("Failed to retrieve results.")
            return

    create_dir = create_folder(args.path, selected_manga['title'])
    post_id = await get_post_id(selected_link)
    meta_chapter = await get_chapters(post_id, referer=selected_link)
    chapter = extract_chapters(str(meta_chapter))

    # Use the chapter range from argparse and the specified path for downloading
    start_chapter, end_chapter = args.chapters
    download_directory = create_dir
    
    print(f"Downloading chapters {start_chapter} to {end_chapter} to directory: {download_directory}")
    
    await download_chapters(chapter, start_chapter, end_chapter, download_directory)

# To call the main function in the async environment
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

