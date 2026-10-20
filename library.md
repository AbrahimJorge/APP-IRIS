# Bibliotecas do Projeto IRIS

Este documento lista todas as bibliotecas Python utilizadas no projeto IRIS, divididas entre bibliotecas instaladas (externas) e bibliotecas nativas (standard library), indicando os arquivos em que estao presentes, seu proposito geral e sua finalidade especifica no projeto.

---

## Bibliotecas Instaladas

### Flet (flet / flet-desktop)
- **Usada nos arquivos:** `main.py`, `components/bottom_nav.py`, `views/camera_view.py`, `views/daltonism_test_view.py`, `views/home_view.py`, `views/image_view.py`, `views/screen_picker_view.py`, `views/settings_view.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para construcao de interfaces graficas de usuario (GUI) modernas e reativas em Python, baseada na arquitetura do Flutter. Neste projeto, ela e usada como o framework principal de toda a interface do aplicativo desktop, gerenciando janelas, paginas, rotas de navegacao, layout e componentes visuais (botoes, cards, dialogos, barra de navegacao inferior e listas).

### OpenCV (opencv-python / cv2)
- **Usada nos arquivos:** `services/camera_service.py`, `services/image_service.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para visao computacional, processamento digital de imagens e captura de video em tempo real. Neste projeto, esta sendo usada para abrir e capturar os frames da webcam (`cv2.VideoCapture`), ler imagens do disco (`cv2.imread`), realizar redimensionamento proporcional de resolucao (`cv2.resize`), converter formatos de cores (BGR para RGB) e compactar os frames em buffers JPEG em memoria para exibicao.

### NumPy (numpy)
- **Usada nos arquivos:** `services/camera_service.py`, `services/image_service.py`, `services/screen_service.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para computacao cientifica e manipulacao de arrays multidimensionais (matrizes) em alta performance. Neste projeto, esta sendo usada para manipular as matrizes de pixels dos frames da camera, imagens carregadas e capturas de tela, permitindo calcular medias de cores de regioes selecionadas, fazer amostragem aleatoria de pixels e converter dados de formato para analise.

### Pillow (PIL / pillow)
- **Usada nos arquivos:** `services/screen_service.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para criacao, edicao e manipulacao de arquivos de imagem em Python. Neste projeto, esta sendo usada no servico de captura de tela flutuante para carregar e recortar imagens com canal alfa (`floating_eye.png`), converter imagens para o formato compativel com Tkinter (`ImageTk.PhotoImage`) e como mecanismo alternativo de captura de tela (`ImageGrab`).

### Pandas (pandas)
- **Usada nos arquivos:** `services/color_dataset.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para analise, estruturacao e manipulacao de dados tabulares em DataFrames. Neste projeto, esta sendo usada para ler o arquivo de base de dados de cores (`colors.csv` local ou remotamente via GitHub), organizando e estruturando os nomes das cores, codigos hexadecimais e coordenadas RGB necessarias para a busca.

### SciPy (scipy)
- **Usada nos arquivos:** `services/color_dataset.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para computacao cientifica, matematica avancada e estruturas de dados espaciais. Neste projeto, esta sendo usada por meio da classe `KDTree` (`scipy.spatial.KDTree`) para indexar os valores RGB do dataset e realizar buscas espaciais de vizinho mais proximo em tempo constante/logaritmico, associando qualquer cor amostrada ao nome catalogado mais proximo.

### MSS (mss)
- **Usada nos arquivos:** `services/screen_service.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para captura de tela (screenshots) multiplataforma ultrarrapida com baixo consumo de processamento. Neste projeto, esta sendo usada para capturar em tempo real a regiao ao redor do cursor do mouse ou a area selecionada pelo usuario na ferramenta flutuante de conta-gotas na tela.

### Pynput (pynput)
- **Usada nos arquivos:** `services/screen_service.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para monitorar e controlar dispositivos de entrada fisicos (mouse e teclado) em nivel global no sistema operacional. Neste projeto, esta sendo usada para escutar eventos globais de movimento e clique do mouse (`mouse.Listener`), permitindo que a ferramenta flutuante acompanhe o cursor e identifique quando e onde o usuario clicou para inspecionar uma cor fora da janela principal.

---

## Bibliotecas Nativas (Standard Library)

### base64
- **Usada nos arquivos:** `services/camera_service.py`, `services/image_service.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para codificar e decodificar dados binarios no formato de texto ASCII (Base64). Neste projeto, esta sendo usada para transformar os buffers binarios de imagem gerados pelo OpenCV em strings Base64 com data URI (`data:image/jpeg;base64,...`), viabilizando a renderizacao direta nos componentes visuais do Flet sem gravar arquivos temporarios no disco.

### collections (Counter)
- **Usada nos arquivos:** `services/camera_service.py`, `services/image_service.py`, `services/screen_service.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para fornecer tipos de dados e colecoes especializadas em Python. Neste projeto, esta sendo usada a classe `Counter` para contabilizar a frequencia das cores identificadas em uma regiao retangular de imagem, camera ou tela, determinando as cores dominantes e suas porcentagens.

### colorsys
- **Usada nos arquivos:** `services/color_dataset.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para realizar conversoes bidirecionais de valores entre diferentes sistemas de representacao de cores (RGB, YIQ, HLS, HSV). Neste projeto, esta sendo usada para converter coordenadas RGB em HLS (`colorsys.rgb_to_hls`), permitindo avaliar matiz, luminosidade e saturacao para classificar as cores em suas familias em portugues (como Preto, Branco, Cinza ou tons coloridos).

### ctypes
- **Usada nos arquivos:** `main.py`, `services/screen_service.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para interoperabilidade com funcoes e bibliotecas dinamicas (DLLs) em C e APIs de baixo nivel do sistema operacional. Neste projeto, esta sendo usada no Windows para definir a escala DPI correta do processo (`SetProcessDpiAwareness`), garantindo sincronia 1:1 entre coordenadas do mouse e da tela, alem de aplicar estilos de janela estendidos (`WS_EX_TRANSPARENT`, `WS_EX_LAYERED`) no menu flutuante.

### json
- **Usada nos arquivos:** `services/i18n_service.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para serializacao e desserializacao de dados estruturados no formato JSON. Neste projeto, esta sendo usada para carregar e salvar a persistencia das configuracoes de idioma do usuario no arquivo `assets/config.json`.

### os
- **Usada nos arquivos:** `services/camera_service.py`, `services/color_dataset.py`, `services/constants/dataset_constants.py`, `services/constants/translate_constants.py`, `services/i18n_service.py`, `services/image_service.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para interagir com funcionalidades do sistema operacional e manipulacao de arquivos e diretorios. Neste projeto, esta sendo usada para construcao dinamica de caminhos de arquivos (`os.path.join`, `os.path.dirname`), verificacao da existencia de arquivos (`os.path.exists`) e criacao automatica de pastas (`os.makedirs`).

### random
- **Usada nos arquivos:** `views/daltonism_test_view.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para geracao de numeros pseudoaleatorios e selecao probabilistica de itens em colecoes. Neste projeto, esta sendo usada para sortear dinamicamente amostras balanceadas de pranchas (`random.sample`) do teste de Ishihara a partir dos diferentes grupos de pranchas disponíveis.

### ssl
- **Usada nos arquivos:** `services/color_dataset.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para criptografia SSL/TLS e gerenciamento de conexoes de rede seguras. Neste projeto, esta sendo usada para criar um contexto HTTPS seguro caso a aplicacao precise baixar a base de dados `colors.csv` do repositorio do GitHub quando o arquivo local nao estiver disponivel.

### sys
- **Usada nos arquivos:** `services/camera_service.py`, `services/image_service.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para acessar variaveis e parametros associados diretamente ao interpretador Python. Neste projeto, esta sendo usada para manipular o caminho de busca de modulos (`sys.path.insert`), possibilitando que os modulos de servico funcionem tanto importados pelo app quanto executados de forma autonoma para testes.

### threading
- **Usada nos arquivos:** `services/camera_service.py`, `services/screen_service.py`, `views/camera_view.py`, `views/image_view.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para execucao concorrente de tarefas atraves de threads e sincronizacao com travas (locks). Neste projeto, esta sendo usada para rodar a captura da webcam e a janela flutuante em segundo plano (`threading.Thread`), alem de sincronizar acessos concorrentes aos quadros de imagem com `threading.Lock`, impedindo que operacoes continuas travem a interface grafica.

### time
- **Usada nos arquivos:** `services/camera_service.py`, `services/screen_service.py`, `views/camera_view.py`, `views/image_view.py`
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve para manipulacao de horarios, medicoes de tempo e pausas de execucao. Neste projeto, esta sendo usada para controlar a taxa de atualizacao de quadros (FPS), calcular intervalos de tempo em acoes de arrasto do cursor e aplicar pausas controladas com `time.sleep()`.

### tkinter
- **Usada nos arquivos:** `services/screen_service.py` (modulo opcional e exclusivo para Desktop)
- **Contexto geral e uso no projeto:**
  Ela e uma biblioteca que serve como o pacote padrao de interface grafica nativa (GUI) do Python para desktop. Neste projeto, e importada de forma condicional para renderizar a janela flutuante sem bordas de captura de tela em `services/screen_service.py` exclusivamente em computadores, sendo desativada em ambientes moveis (Android/iOS) onde o Tkinter nao esta presente. Na tela de imagem, a selecao de arquivos e feita pelo componente multiplataforma `ft.FilePicker` do Flet.
