"""
Module pour afficher des PDF dans Streamlit avec contrôles d'approbation
"""
import base64
import os

def create_pdf_viewer_html(pdf_path, token, show_buttons=True):
    """
    Crée un viewer PDF avec PDF.js et boutons d'approbation
    """
    
    # Lire le PDF et encoder en base64
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()
    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
    
    # HTML avec PDF.js depuis CDN
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Visualiseur PDF</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f5f5;
                display: flex;
                flex-direction: column;
                height: 100vh;
            }}
            
            .pdf-container {{
                flex: 1;
                display: flex;
                flex-direction: column;
                background: white;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin: 20px;
                border-radius: 10px;
                overflow: hidden;
            }}
            
            .pdf-toolbar {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            
            .toolbar-left {{
                display: flex;
                gap: 15px;
                align-items: center;
            }}
            
            .toolbar-btn {{
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                padding: 8px 15px;
                border-radius: 5px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 14px;
                font-weight: 500;
            }}
            
            .toolbar-btn:hover {{
                background: rgba(255,255,255,0.3);
                transform: translateY(-2px);
            }}
            
            .page-info {{
                background: rgba(255,255,255,0.2);
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
            }}
            
            .zoom-controls {{
                display: flex;
                gap: 10px;
                align-items: center;
            }}
            
            .zoom-btn {{
                width: 35px;
                height: 35px;
                border-radius: 50%;
                background: rgba(255,255,255,0.2);
                border: 1px solid rgba(255,255,255,0.3);
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
            }}
            
            .zoom-btn:hover {{
                background: rgba(255,255,255,0.3);
            }}
            
            #pdf-viewer {{
                flex: 1;
                overflow: auto;
                background: #fafafa;
                display: flex;
                justify-content: center;
                padding: 20px;
            }}
            
            #pdf-canvas {{
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                background: white;
                max-width: 100%;
                height: auto;
            }}
            
            .approval-bar {{
                padding: 25px;
                background: white;
                border-top: 1px solid #e5e5e5;
                display: flex;
                justify-content: center;
                gap: 20px;
                box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
            }}
            
            .approval-btn {{
                padding: 15px 40px;
                font-size: 16px;
                font-weight: 600;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                text-decoration: none;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }}
            
            .approve-btn {{
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
                color: white;
            }}
            
            .approve-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(72, 187, 120, 0.3);
            }}
            
            .reject-btn {{
                background: linear-gradient(135deg, #f56565 0%, #e53e3e 100%);
                color: white;
            }}
            
            .reject-btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(245, 101, 101, 0.3);
            }}
            
            .loading {{
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 400px;
                color: #666;
            }}
            
            .spinner {{
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 50px;
                height: 50px;
                animation: spin 1s linear infinite;
                margin-bottom: 20px;
            }}
            
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            
            @media print {{
                .pdf-toolbar, .approval-bar {{
                    display: none !important;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="pdf-container">
            <div class="pdf-toolbar">
                <div class="toolbar-left">
                    <button class="toolbar-btn" onclick="previousPage()">⬅️ Précédent</button>
                    <span class="page-info">
                        Page <span id="page-num">1</span> / <span id="page-count">-</span>
                    </span>
                    <button class="toolbar-btn" onclick="nextPage()">Suivant ➡️</button>
                </div>
                
                <div class="zoom-controls">
                    <button class="zoom-btn" onclick="zoomOut()">➖</button>
                    <span style="margin: 0 10px;">Zoom: <span id="zoom-level">100</span>%</span>
                    <button class="zoom-btn" onclick="zoomIn()">➕</button>
                    <button class="toolbar-btn" onclick="fitPage()">📄 Ajuster</button>
                </div>
                
                <div>
                    <button class="toolbar-btn" onclick="downloadPDF()">💾 Télécharger</button>
                    <button class="toolbar-btn" onclick="printPDF()">🖨️ Imprimer</button>
                </div>
            </div>
            
            <div id="pdf-viewer">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Chargement du document PDF...</p>
                </div>
                <canvas id="pdf-canvas" style="display: none;"></canvas>
            </div>
        </div>
    """
    
    if show_buttons:
        html += f"""
        <div class="approval-bar">
            <a href="?token={token}&action=approve" class="approval-btn approve-btn">
                ✅ APPROUVER
            </a>
            <a href="?token={token}&action=reject" class="approval-btn reject-btn">
                ❌ REFUSER
            </a>
        </div>
        """
    
    html += f"""
        <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
        <script>
            // Configuration PDF.js
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            
            // Variables globales
            let pdfDoc = null;
            let pageNum = 1;
            let pageRendering = false;
            let pageNumPending = null;
            let scale = 1.5;
            const canvas = document.getElementById('pdf-canvas');
            const ctx = canvas.getContext('2d');
            
            // Données PDF en base64
            const pdfData = atob('{pdf_base64}');
            
            // Convertir en Uint8Array
            const pdfArray = new Uint8Array(pdfData.length);
            for (let i = 0; i < pdfData.length; i++) {{
                pdfArray[i] = pdfData.charCodeAt(i);
            }}
            
            // Charger le PDF
            pdfjsLib.getDocument({{data: pdfArray}}).promise.then(function(pdfDoc_) {{
                pdfDoc = pdfDoc_;
                document.getElementById('page-count').textContent = pdfDoc.numPages;
                
                // Masquer le loading et afficher le canvas
                document.querySelector('.loading').style.display = 'none';
                canvas.style.display = 'block';
                
                // Afficher la première page
                renderPage(pageNum);
            }}).catch(function(error) {{
                console.error('Erreur chargement PDF:', error);
                document.querySelector('.loading').innerHTML = '<p style="color: red;">Erreur lors du chargement du PDF</p>';
            }});
            
            function renderPage(num) {{
                pageRendering = true;
                
                pdfDoc.getPage(num).then(function(page) {{
                    const viewport = page.getViewport({{scale: scale}});
                    canvas.height = viewport.height;
                    canvas.width = viewport.width;
                    
                    const renderContext = {{
                        canvasContext: ctx,
                        viewport: viewport
                    }};
                    
                    const renderTask = page.render(renderContext);
                    
                    renderTask.promise.then(function() {{
                        pageRendering = false;
                        if (pageNumPending !== null) {{
                            renderPage(pageNumPending);
                            pageNumPending = null;
                        }}
                    }});
                }});
                
                document.getElementById('page-num').textContent = num;
            }}
            
            function queueRenderPage(num) {{
                if (pageRendering) {{
                    pageNumPending = num;
                }} else {{
                    renderPage(num);
                }}
            }}
            
            function previousPage() {{
                if (pageNum <= 1) return;
                pageNum--;
                queueRenderPage(pageNum);
            }}
            
            function nextPage() {{
                if (pageNum >= pdfDoc.numPages) return;
                pageNum++;
                queueRenderPage(pageNum);
            }}
            
            function zoomIn() {{
                scale = Math.min(scale + 0.25, 3);
                document.getElementById('zoom-level').textContent = Math.round(scale * 100);
                queueRenderPage(pageNum);
            }}
            
            function zoomOut() {{
                scale = Math.max(scale - 0.25, 0.5);
                document.getElementById('zoom-level').textContent = Math.round(scale * 100);
                queueRenderPage(pageNum);
            }}
            
            function fitPage() {{
                scale = 1.0;
                document.getElementById('zoom-level').textContent = 100;
                queueRenderPage(pageNum);
            }}
            
            function downloadPDF() {{
                const link = document.createElement('a');
                link.href = 'data:application/pdf;base64,{pdf_base64}';
                link.download = 'document.pdf';
                link.click();
            }}
            
            function printPDF() {{
                window.print();
            }}
            
            // Raccourcis clavier
            document.addEventListener('keydown', function(e) {{
                switch(e.key) {{
                    case 'ArrowLeft':
                        previousPage();
                        break;
                    case 'ArrowRight':
                        nextPage();
                        break;
                    case '+':
                        zoomIn();
                        break;
                    case '-':
                        zoomOut();
                        break;
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    return html

def create_simple_pdf_viewer(pdf_path):
    """
    Version simplifiée pour affichage dans Streamlit
    """
    with open(pdf_path, 'rb') as f:
        pdf_data = f.read()
    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
    
    # Simple iframe avec embed PDF
    html = f"""
    <iframe 
        src="data:application/pdf;base64,{pdf_base64}" 
        width="100%" 
        height="800px"
        style="border: none; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
    </iframe>
    """
    
    return html