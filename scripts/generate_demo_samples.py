"""Generates synthetic demo images for VisionVoice AI presentation."""

import os
from PIL import Image, ImageDraw


def generate_all_samples():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    demo_dir = os.path.join(base_dir, "demo", "samples")
    os.makedirs(demo_dir, exist_ok=True)

    # 1. University Webpage
    img1 = Image.new("RGB", (900, 600), color=(248, 250, 252))
    d1 = ImageDraw.Draw(img1)
    d1.rectangle([(0, 0), (900, 70)], fill=(30, 41, 59))
    d1.text((30, 24), "METRO STATE UNIVERSITY - ADMISSIONS PORTAL", fill=(255, 255, 255))
    d1.text((700, 26), "www.metrostate.edu", fill=(148, 163, 184))

    d1.text((50, 110), "Undergraduate Admissions 2026-2027", fill=(15, 23, 42))
    d1.text((50, 150), "Join our world-class engineering and computing programs.", fill=(71, 85, 105))

    d1.rectangle([(50, 190), (850, 360)], fill=(241, 245, 249), outline=(203, 213, 225), width=2)
    d1.text((70, 210), "IMPORTANT ADMISSION DEADLINES", fill=(15, 23, 42))
    d1.text((70, 250), "Application deadline: September 30, 2026", fill=(225, 29, 72))
    d1.text((70, 285), "Financial Aid Priority: October 15, 2026", fill=(51, 65, 85))
    d1.text((70, 320), "Online application available 24/7 at portal.metrostate.edu", fill=(51, 65, 85))

    d1.rectangle([(50, 390), (250, 450)], fill=(37, 99, 235))
    d1.text((85, 415), "APPLY NOW", fill=(255, 255, 255))

    d1.rectangle([(270, 390), (490, 450)], fill=(226, 232, 240))
    d1.text((295, 415), "Download Brochure", fill=(15, 23, 42))

    d1.text((50, 520), "Contact Admissions: admissions@metrostate.edu | Tel: (555) 019-2831", fill=(100, 116, 139))
    p1 = os.path.join(demo_dir, "university_admission.png")
    img1.save(p1)
    print(f"Created: {p1}")

    # 2. Restaurant Menu
    img2 = Image.new("RGB", (850, 650), color=(254, 252, 248))
    d2 = ImageDraw.Draw(img2)
    d2.rectangle([(0, 0), (850, 90)], fill=(41, 37, 36))
    d2.text((250, 25), "THE ARTISAN BISTRO & GRILL", fill=(250, 245, 235))
    d2.text((320, 60), "DINNER SELECTIONS & WINE", fill=(214, 211, 209))

    d2.text((60, 120), "STARTERS & APPETIZERS", fill=(120, 53, 15))
    d2.text((60, 155), "Truffle Wild Mushroom Bruschetta - $14.50", fill=(28, 25, 23))
    d2.text((60, 185), "Crispy Calamari with Citrus Aioli - $16.00", fill=(28, 25, 23))
    d2.text((60, 215), "Roasted Tomato & Basil Soup - $9.50", fill=(28, 25, 23))

    d2.text((60, 270), "CHEF SPECIAL MAIN COURSES", fill=(120, 53, 15))
    d2.text((60, 305), "Pan-Seared Atlantic Salmon with Asparagus - $28.00", fill=(28, 25, 23))
    d2.text((60, 335), "Prime Wagyu Beef Burger with Truffle Fries - $24.00", fill=(28, 25, 23))
    d2.text((60, 365), "Creamy Wild Mushroom & Herb Risotto - $22.50", fill=(28, 25, 23))

    d2.rectangle([(60, 430), (320, 490)], fill=(180, 83, 9))
    d2.text((115, 455), "ORDER ONLINE NOW", fill=(255, 255, 255))
    d2.text((60, 530), "Gluten-Free and Vegan preparations available on request.", fill=(87, 83, 78))
    d2.text((60, 560), "Visit: www.artisanbistro.com | Delivery available until 10:00 PM", fill=(120, 113, 108))
    p2 = os.path.join(demo_dir, "restaurant_menu.png")
    img2.save(p2)
    print(f"Created: {p2}")

    # 3. Product Label
    img3 = Image.new("RGB", (700, 750), color=(255, 255, 255))
    d3 = ImageDraw.Draw(img3)
    d3.rectangle([(15, 15), (685, 735)], outline=(0, 0, 0), width=3)
    d3.text((150, 40), "NATURE CRAFT ORGANIC GRANOLA", fill=(0, 0, 0))
    d3.text((200, 75), "HONEY ROASTED ALMOND & CHIA", fill=(80, 80, 80))
    d3.line([(30, 110), (670, 110)], fill=(0, 0, 0), width=4)

    d3.text((40, 130), "Nutrition Facts", fill=(0, 0, 0))
    d3.text((40, 170), "Serving Size: 1/2 cup (55g)", fill=(0, 0, 0))
    d3.text((40, 200), "Servings Per Container: about 8", fill=(0, 0, 0))
    d3.line([(30, 230), (670, 230)], fill=(0, 0, 0), width=6)

    d3.text((40, 250), "Amount Per Serving: Calories 210", fill=(0, 0, 0))
    d3.line([(30, 280), (670, 280)], fill=(0, 0, 0), width=2)
    d3.text((40, 295), "Total Fat 8g (10% DV)", fill=(0, 0, 0))
    d3.text((40, 325), "Sodium 115mg (5% DV)", fill=(0, 0, 0))
    d3.text((40, 355), "Total Carbohydrate 32g (12% DV)", fill=(0, 0, 0))
    d3.text((40, 385), "Protein 6g", fill=(0, 0, 0))
    d3.line([(30, 420), (670, 420)], fill=(0, 0, 0), width=4)

    d3.text((40, 440), "INGREDIENTS: Whole grain rolled oats, organic wildflower honey,", fill=(30, 30, 30))
    d3.text((40, 470), "almonds, chia seeds, cold-pressed sunflower oil, sea salt.", fill=(30, 30, 30))
    d3.text((40, 520), "ALLERGEN WARNING: Contains tree nuts (almonds).", fill=(180, 20, 20))
    d3.text((40, 560), "Net Weight: 16 oz (454g)", fill=(0, 0, 0))
    d3.text((40, 600), "Expiry Date: November 15, 2026", fill=(0, 0, 0))
    d3.text((40, 640), "Manufactured by NatureCraft Foods Inc., Denver CO 80202", fill=(100, 100, 100))
    p3 = os.path.join(demo_dir, "product_label.png")
    img3.save(p3)
    print(f"Created: {p3}")

    # 4. General Desktop Screenshot
    img4 = Image.new("RGB", (950, 600), color=(18, 18, 24))
    d4 = ImageDraw.Draw(img4)
    d4.rectangle([(0, 0), (950, 45)], fill=(30, 30, 40))
    d4.text((25, 14), "VisionVoice Studio - Visual Accessibility Workspace", fill=(220, 220, 230))

    d4.rectangle([(0, 45), (200, 600)], fill=(24, 24, 32))
    d4.text((20, 65), "PROJECT EXPLORER", fill=(130, 130, 150))
    d4.text((25, 100), "> app/", fill=(180, 180, 200))
    d4.text((25, 130), "> hardware/", fill=(180, 180, 200))
    d4.text((25, 160), "> vision/", fill=(180, 180, 200))
    d4.text((25, 190), "> tests/", fill=(180, 180, 200))
    d4.text((25, 230), "ACTIVE BACKEND:", fill=(100, 180, 255))
    d4.text((25, 260), "Local CPU Fallback", fill=(0, 220, 130))

    d4.text((230, 70), "def initialize_multimodal_pipeline():", fill=(255, 198, 109))
    d4.text((260, 105), "# On-device multimodal reasoning without cloud API", fill=(128, 128, 128))
    d4.text((260, 140), "backend = hardware_detector.inspect()", fill=(204, 120, 50))
    d4.text((260, 175), "print('Local CPU execution safe and verified.')", fill=(106, 171, 115))
    d4.text((260, 210), "return backend.is_npu_available", fill=(204, 120, 50))

    d4.rectangle([(200, 380), (950, 570)], fill=(12, 12, 16))
    d4.text((220, 395), "TERMINAL: PowerShell 7", fill=(150, 150, 170))
    d4.text((220, 430), "PS C:\\Project> pytest tests/ --verbose", fill=(220, 220, 220))
    d4.text((220, 465), "[PASS] test_hardware_detection", fill=(80, 220, 100))
    d4.text((220, 495), "[PASS] test_ocr_onnx_pipeline", fill=(80, 220, 100))
    d4.text((220, 525), "Summary: 10 passed in 1.42s", fill=(255, 255, 255))

    d4.rectangle([(0, 570), (950, 600)], fill=(0, 122, 204))
    d4.text((20, 578), "Ready | UTF-8 | Python 3.14 | Memory: 4.2 GB / 7.6 GB", fill=(255, 255, 255))
    p4 = os.path.join(demo_dir, "desktop_screenshot.png")
    img4.save(p4)
    print(f"Created: {p4}")

    print("All 4 demo samples created successfully.")


if __name__ == "__main__":
    generate_all_samples()
