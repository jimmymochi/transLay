import fitz

def generate_pdf():
    doc = fitz.open()
    page = doc.new_page(width=595, height=842) # A4 規格
    
    # 1. 繪製跨欄標題 (Title)
    page.insert_textbox(
        fitz.Rect(50, 50, 545, 100), 
        "An Amazing Academic Paper on Layout-Preserving Translation", 
        fontsize=15, 
        align=1
    )
    
    # 2. 繪製左欄第一段
    left_text_1 = (
        "This is the first paragraph of the left column. We will discuss the challenge of layout-preserving "
        "translation of academic papers. Most online translation systems extract text and lose column structures. "
        "This causes text overlap and cross-column reading issues. Our layout-aware fitter solves this problem."
    )
    page.insert_textbox(fitz.Rect(50, 120, 280, 300), left_text_1, fontsize=9.5)
    
    # 3. 繪製左欄第二段
    left_text_2 = (
        "Here is the second paragraph of the left column. We introduce a five-stage fitting pipeline. "
        "It compresses line height, expands bounding box safely, shrinks font size, and uses overflow manager "
        "for graceful fallback in the appendix."
    )
    page.insert_textbox(fitz.Rect(50, 320, 280, 550), left_text_2, fontsize=9.5)
    
    # 4. 繪製右欄第一段
    right_text_1 = (
        "Now we look at the right column of the document. Obstacle detection is a critical first step. "
        "It detects images, tables, drawings, and safe zones. Any expanded box must perform collision "
        "detection against these obstacles to avoid overlapping."
    )
    page.insert_textbox(fitz.Rect(315, 120, 545, 300), right_text_1, fontsize=9.5)
    
    # 5. 繪製右欄模擬圖片障礙物 (Figure Hard Obstacle)
    page.draw_rect(fitz.Rect(315, 320, 545, 450), color=(0.8, 0.1, 0.1), width=1, fill=(0.95, 0.95, 0.95))
    page.insert_textbox(fitz.Rect(315, 325, 545, 445), "Figure 1: BBox Obstacle Demonstration Block", fontsize=9.0, align=1)
    
    # 6. 繪製右欄圖片下方之第二段
    right_text_2 = (
        "Below the figure, we place some concluding text. Our results demonstrate high layout preservation. "
        "The translation output is highly legible and readable by academic professionals in Taiwan."
    )
    page.insert_textbox(fitz.Rect(315, 470, 545, 600), right_text_2, fontsize=9.5)
    
    # 7. 頁尾頁碼
    page.insert_text(fitz.Point(280, 800), "Page 1", fontsize=8.0)
    
    doc.save("test_input.pdf")
    doc.close()
    print("Success generating test_input.pdf for integration verification!")

if __name__ == "__main__":
    generate_pdf()
