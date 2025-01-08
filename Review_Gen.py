
import os
from pathlib import Path

# Define paths
pwd = os.getcwd()
root = Path(pwd)
pngs = root / 'pngs'

mi_pngs = pngs / 'mi_pngs'
ai_pngs = pngs / 'ai_pngs'
ri_pngs = pngs / 'ri_pngs'

# Get sorted lists of images
mi_images = sorted(mi_pngs.glob('*.png'))
ai_images = sorted(ai_pngs.glob('*.png'))
ri_images = sorted(ri_pngs.glob('*.png'))

# Group `mi_pngs` images by `_mi` and `_srafmi`
mi_image_groups = {}
for img in mi_images:
    if "_srafmi" in img.stem:
        base_name = img.stem.replace("_srafmi", "")
        if base_name not in mi_image_groups:
            mi_image_groups[base_name] = {"mi": None, "srafmi": None}
        mi_image_groups[base_name]["srafmi"] = img
    elif "_mi" in img.stem:
        base_name = img.stem.replace("_mi", "")
        if base_name not in mi_image_groups:
            mi_image_groups[base_name] = {"mi": None, "srafmi": None}
        mi_image_groups[base_name]["mi"] = img

# Sort the groups by their base names
sorted_base_names = sorted(mi_image_groups.keys())
mi_image_groups = {base_name: mi_image_groups[base_name] for base_name in sorted_base_names}

# HTML Template
def generate_html(mi_image_groups, ai_images, ri_images, output_path="review.html"):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Image Review</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                padding: 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                text-align: center;
                padding: 10px;
                border: 1px solid #ddd;
            }
            img {
                max-width: 150px;
                height: auto;
            }
            .filename {
                font-size: 12px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <h1>Image Review</h1>
        <table>
            <thead>
                <tr>
                    <th>MI Image</th>
                    <th>MI (SRAF) Image</th>
                    <th>AI Image</th>
                    <th>RI Image</th>
                </tr>
            </thead>
            <tbody>
    """

    # Add rows for each set of images
    for base_name, mi_imgs in mi_image_groups.items():
        # Match AI and RI images using the appropriate suffixes
        ai_img = next((img for img in ai_images if img.stem == base_name + "_oi"), None)
        ri_img = next((img for img in ri_images if img.stem == base_name + "_ri"), None)

        # Extract MI and MI (SRAF) images
        mi_img = mi_imgs["mi"]
        mi_sraf_img = mi_imgs["srafmi"]

        html_content += "<tr>"
        
        # MI Image
        if mi_img:
            html_content += f"""
            <td>
                <img src="{mi_img}" alt="MI Image"><br>
                <span class="filename">{mi_img.name}</span>
            </td>
            """
        else:
            html_content += "<td>No Image</td>"
        
        # MI (SRAF) Image
        if mi_sraf_img:
            html_content += f"""
            <td>
                <img src="{mi_sraf_img}" alt="MI SRAF Image"><br>
                <span class="filename">{mi_sraf_img.name}</span>
            </td>
            """
        else:
            html_content += "<td>No Image</td>"
        
        # AI Image
        if ai_img:
            html_content += f"""
            <td>
                <img src="{ai_img}" alt="AI Image"><br>
                <span class="filename">{ai_img.name}</span>
            </td>
            """
        else:
            html_content += "<td>No Image</td>"
        
        # RI Image
        if ri_img:
            html_content += f"""
            <td>
                <img src="{ri_img}" alt="RI Image"><br>
                <span class="filename">{ri_img.name}</span>
            </td>
            """
        else:
            html_content += "<td>No Image</td>"

        html_content += "</tr>"

    # Close HTML
    html_content += """
            </tbody>
        </table>
    </body>
    </html>
    """

    # Write to output file
    with open(output_path, 'w') as f:
        f.write(html_content)
    print(f"HTML review file generated: {output_path}")

# Generate HTML
generate_html(mi_image_groups, ai_images, ri_images)
