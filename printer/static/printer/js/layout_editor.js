window.addEventListener('DOMContentLoaded', () => {

    // --- 1. REFERÊNCIAS AOS ELEMENTOS ---
    const canvas = document.getElementById('label-canvas');
    const propertyPanel = document.getElementById('property-panel');
    const form = document.querySelector('#content-main form');
    const widthField = document.getElementById('id_largura_mm');
    const heightField = document.getElementById('id_altura_mm');
    const jsonField = document.getElementById('id_layout_json'); // Agora deve funcionar
    const addTextBtn = document.getElementById('add-text-btn');
    const addQrBtn = document.getElementById('add-qr-btn');
    const removeElementBtn = document.getElementById('remove-element-btn');
    const propDataSource = document.getElementById('prop-data-source');
    const propCustomTextWrapper = document.getElementById('custom-text-wrapper');
    const propCustomText = document.getElementById('prop-custom-text');
    const propFontSizeWrapper = document.getElementById('font-size-wrapper');
    const propFontSize = document.getElementById('prop-font-size');
    const propFontWeight = document.getElementById('prop-font-weight');
    const propBackground = document.getElementById('prop-background');

    const propFontWeightWrapper = document.getElementById('font-weight-wrapper');
    
    const propWrapTextWrapper = document.getElementById('wrap-text-wrapper');
    const propWrapText = document.getElementById('prop-wrap-text');

    let selectedElement = null; 
    const PIXELS_PER_MM = 3.7795; 
    const ZOOM_FACTOR = 2.0; 
    const FINAL_RATIO = PIXELS_PER_MM * ZOOM_FACTOR;

    // --- 2. FUNÇÕES PRINCIPAIS ---

    // ---- INÍCIO DA CORREÇÃO ----
    // O Django agora renderiza o campo. Vamos escondê-lo.
    if (jsonField) {
        // Encontra o 'form-row' pai do <textarea> e o esconde
        const formRow = jsonField.closest('.form-row');
        if (formRow) {
            formRow.style.display = 'none';
        } else {
            // Plano B se não encontrar o form-row (improvável)
            jsonField.style.display = 'none';
        }
    } else {
        // Esta mensagem de erro agora é a mais importante
        console.error("ERRO CRÍTICO: Campo 'id_layout_json' não foi encontrado no HTML! O salvamento falhará.");
    }
    // ---- FIM DA CORREÇÃO ----
    
    function updateCanvasSize() {
        if (!widthField || !heightField || !canvas) return;
        const widthMM = parseFloat(widthField.value) || 50;
        const heightMM = parseFloat(heightField.value) || 50;
        canvas.style.width = `${widthMM * FINAL_RATIO}px`;
        canvas.style.height = `${heightMM * FINAL_RATIO}px`;
    }

    function loadLayout() {
        if (!jsonField || !canvas) return;
        let layoutData = [];
        try {
            if (jsonField.value) {
                layoutData = JSON.parse(jsonField.value);
            } else {
                layoutData = [];
            }
        } catch (e) {
            console.error('Erro ao ler o JSON do layout:', e);
            layoutData = [];
        }
        canvas.innerHTML = ''; 
        layoutData.forEach(createElement);
    }

    function saveLayout() {
        if (!jsonField || !canvas) return;
        const elements = canvas.querySelectorAll('.label-element');
        const layoutData = [];
        
        elements.forEach(el => {
            const x_mm = parseFloat(el.dataset.x) / FINAL_RATIO;
            const y_mm = parseFloat(el.dataset.y) / FINAL_RATIO;
            const width_px = parseFloat(el.style.width);
            const height_px = parseFloat(el.style.height);

            const elementData = {
                id: el.id, type: el.dataset.type, x: x_mm, y: y_mm,
                size: el.dataset.type === 'qrcode' ? (width_px / FINAL_RATIO) : undefined, 
                width: el.dataset.type === 'text' ? (width_px / FINAL_RATIO) : undefined,
                height: el.dataset.type === 'text' ? (height_px / FINAL_RATIO) : undefined,
                data_source: el.dataset.dataSource,
                custom_text: el.dataset.customText,
                font_size: parseInt(el.style.fontSize) || 12,
                font_weight: el.style.fontWeight,
                has_background: el.classList.contains('has-background'),
                allow_wrap: el.dataset.allowWrap === 'true'
            };
            layoutData.push(elementData);
        });
        
        jsonField.value = JSON.stringify(layoutData, null, 2);
        console.log('Layout salvo no JSONField:', jsonField.value);
    }
    
    function createElement(config) {
        const el = document.createElement('div');
        el.id = config.id || `el-${Date.now()}`;
        el.className = 'label-element';
        el.dataset.type = config.type;
        const x_px = (config.x || 0) * FINAL_RATIO;
        const y_px = (config.y || 0) * FINAL_RATIO;
        let width_px, height_px;
        if (config.type === 'qrcode') {
            width_px = (config.size || 25) * FINAL_RATIO;
            height_px = (config.size || 25) * FINAL_RATIO;
        } else {
            width_px = (config.width || 40) * FINAL_RATIO;
            height_px = (config.height || 8) * FINAL_RATIO;
        }
        el.style.width = `${width_px}px`;
        el.style.height = `${height_px}px`;
        el.style.transform = `translate(${x_px}px, ${y_px}px)`;
        el.dataset.x = x_px;
        el.dataset.y = y_px;
        config.allow_wrap = config.allow_wrap || false;

        updateElementVisuals(el, config);
        el.addEventListener('click', (e) => {
            e.stopPropagation();
            selectElement(el);
        });
        canvas.appendChild(el);
    }

    function updateElementVisuals(el, config) {
        el.dataset.dataSource = config.data_source || 'titulo';
        el.dataset.customText = config.custom_text || '';
        if (config.type === 'text') {
            el.style.fontSize = `${config.font_size || 12}pt`;
            el.style.fontWeight = config.font_weight || 'normal';
            el.style.color = config.has_background ? '#fff' : '#000';
            
            // Aplica/remove a classe de quebra de linha
            el.dataset.allowWrap = config.allow_wrap || false;
            if (config.allow_wrap) {
                el.classList.add('allow-wrap');
            } else {
                el.classList.remove('allow-wrap');
            }
            
            // Texto de placeholder
            if (config.data_source === 'custom') {
                el.innerText = config.custom_text || '[Texto Fixo]';
            } else if (config.data_source === 'url') {
                el.innerText = '[URL]';
            } else {
                el.innerText = '[TÍTULO]';
            }
        }
        if (config.has_background) {
            el.classList.add('has-background');
        } else {
            el.classList.remove('has-background');
        }
    }

    function selectElement(el) {
        if (selectedElement) {
            selectedElement.classList.remove('selected');
        }
        selectedElement = el;
        if (!el) {
            propertyPanel.style.display = 'none';
            return;
        }
        
        el.classList.add('selected');
        propertyPanel.style.display = 'block';
        
        const isText = el.dataset.type === 'text';

        // Preenche o painel
        propDataSource.value = el.dataset.dataSource || 'titulo';
        propCustomText.value = el.dataset.customText || '';
        propBackground.checked = el.classList.contains('has-background');
        
        // --- MOSTRA/ESCONDE CAMPOS DE TEXTO ---
        propFontSize.value = parseInt(el.style.fontSize) || 12;
        propFontWeight.checked = (el.style.fontWeight === 'bold');
        propWrapText.checked = (el.dataset.allowWrap === 'true'); // <-- LÊ A FLAG

        propFontSizeWrapper.style.display = isText ? 'block' : 'none';
        propFontWeightWrapper.style.display = isText ? 'block' : 'none';
        propWrapTextWrapper.style.display = isText ? 'block' : 'none'; // <-- MOSTRA/ESCONDE
        
        propCustomTextWrapper.style.display = (propDataSource.value === 'custom') ? 'block' : 'none';
    }

    // --- 3. EVENT LISTENERS ---
    if (widthField) widthField.addEventListener('change', updateCanvasSize);
    if (heightField) heightField.addEventListener('change', updateCanvasSize);
    
    if (addTextBtn) {
        addTextBtn.addEventListener('click', () => {
            createElement({
                type: 'text', data_source: 'titulo', x: 5, y: 5,
                width: 40, height: 8, font_size: 12,
                font_weight: 'bold', has_background: true
            });
        });
    }
    
    if (addQrBtn) {
        addQrBtn.addEventListener('click', () => {
            createElement({
                type: 'qrcode', data_source: 'url', x: 12.5, y: 15, size: 25
            });
        });
    }

    if (removeElementBtn) {
        removeElementBtn.addEventListener('click', () => {
            if (selectedElement) {
                selectedElement.remove();
                selectElement(null); 
            }
        });
    }

    if (canvas) {
        canvas.addEventListener('click', () => {
            selectElement(null);
        });
    }

    if (propertyPanel) {
        propertyPanel.addEventListener('change', (e) => {
            if (!selectedElement) return;
            
            // O objeto 'config' agora inclui o 'type' do elemento
            const config = {
                type: selectedElement.dataset.type, // <-- A LINHA QUE FALTAVA
                data_source: propDataSource.value,
                custom_text: propCustomText.value,
                font_size: parseInt(propFontSize.value),
                font_weight: propFontWeight.checked ? 'bold' : 'normal',
                has_background: propBackground.checked,
                allow_wrap: propWrapText.checked // <-- LÊ A FLAG
            };
            
            propCustomTextWrapper.style.display = (config.data_source === 'custom') ? 'block' : 'none';
            
            // Agora, 'updateElementVisuals' receberá o 'config.type'
            // e aplicará as mudanças de fonte, negrito e cor.
            updateElementVisuals(selectedElement, config);
        });
    }
    
    if (form) {
        form.addEventListener('submit', () => {
            saveLayout(); 
        });
    } else {
        console.error("ERRO CRÍTICO: Formulário admin '#content-main form' não encontrado!");
    }
    
    // --- 4. INICIALIZAÇÃO ---
    // Esta verificação agora deve passar
    if (canvas && widthField && heightField && jsonField) {
        updateCanvasSize();
        loadLayout();
    } else {
        console.error("Não foi possível inicializar o editor. Elementos essenciais (canvas, campos de tamanho ou json) estão faltando.");
    }

    // --- 5. LÓGICA DE ARRASTAR E SOLTAR (interact.js) ---
    if (typeof interact === 'undefined') {
        console.error("Biblioteca 'interact.js' não foi carregada. Arrastar e soltar não funcionará.");
        return;
    }

    interact('.label-element')
        .draggable({
            listeners: {
                move(event) {
                    const target = event.target;
                    let x = (parseFloat(target.dataset.x) || 0) + event.dx;
                    let y = (parseFloat(target.dataset.y) || 0) + event.dy;
                    target.style.transform = `translate(${x}px, ${y}px)`;
                    target.dataset.x = x;
                    target.dataset.y = y;
                }
            },
            modifiers: [
                interact.modifiers.restrictRect({
                    restriction: 'parent'
                })
            ],
            inertia: false
        })
        .resizable({
            edges: { left: true, right: true, bottom: true, top: true },
            listeners: {
                move(event) {
                    let target = event.target;
                    let x = (parseFloat(target.dataset.x) || 0);
                    let y = (parseFloat(target.dataset.y) || 0);
                    target.style.width = `${event.rect.width}px`;
                    target.style.height = `${event.rect.height}px`;
                    x += event.deltaRect.left;
                    y += event.deltaRect.top;
                    target.style.transform = `translate(${x}px, ${y}px)`;
                    target.dataset.x = x;
                    target.dataset.y = y;
                }
            },
            modifiers: [
                interact.modifiers.restrictEdges({
                    outer: 'parent'
                }),
                interact.modifiers.restrictSize({
                    min: { width: 10 * FINAL_RATIO, height: 5 * FINAL_RATIO }
                })
            ],
            inertia: false
        });
});