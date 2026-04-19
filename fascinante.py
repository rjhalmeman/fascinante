import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
import json
import subprocess
from datetime import datetime
import re
import webbrowser  # Nova importação para abrir o navegador

# ==========================================
# CONFIGURAÇÕES DE CORES
# ==========================================
BG_COLOR = "#f4f7f6"
WHITE = "#ffffff"
PRIMARY_BLUE = "#0066cc"
DARK_BLUE = "#004080"
LIGHT_BLUE = "#e6f0ff"
TEXT_COLOR = "#333333"
GREEN_BTN = "#28a745" # Cor para o botão de abrir link

# ==========================================
# LÓGICA PRINCIPAL DO APLICATIVO
# ==========================================
class AppFascinante:
    def __init__(self, root, repo_path):
        self.root = root
        self.repo_path = repo_path
        self.csv_path = os.path.join(repo_path, 'fascinante.csv')
        self.registros = []

        # Configurações da Janela Principal (Aumentada)
        self.root.title("Extrator e Gerenciador - Projeto Fascinante")
        self.root.geometry("1100x850") 
        self.root.configure(bg=BG_COLOR)
        
        # Intercepta o fechamento da janela para executar o Git Push
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.setup_ui()
        self.carregar_csv()

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'), background=PRIMARY_BLUE, foreground=WHITE)
        style.configure("Treeview", font=('Arial', 10), rowheight=25, fieldbackground=WHITE)
        style.map('Treeview', background=[('selected', DARK_BLUE)])

        # --- Cabeçalho ---
        header = tk.Frame(self.root, bg=DARK_BLUE, pady=15)
        header.pack(fill=tk.X)
        tk.Label(header, text="Extrator de Links (Git Integrado)", bg=DARK_BLUE, fg=WHITE, font=('Arial', 16, 'bold')).pack()

        # --- Seção Extração ---
        frame_extracao = tk.Frame(self.root, bg=WHITE, bd=1, relief=tk.SOLID, padx=15, pady=15)
        frame_extracao.pack(fill=tk.X, padx=20, pady=15)

        tk.Label(frame_extracao, text="Cole o texto do e-mail abaixo:", bg=WHITE, fg=DARK_BLUE, font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))
        
        self.text_input = tk.Text(frame_extracao, height=5, font=('Arial', 10), bd=1, relief=tk.SOLID)
        self.text_input.pack(fill=tk.X, pady=5)
        
        btn_extrair = tk.Button(frame_extracao, text="Extrair e Adicionar", bg=PRIMARY_BLUE, fg=WHITE, font=('Arial', 10, 'bold'), relief=tk.FLAT, command=self.extrair_dados)
        btn_extrair.pack(anchor=tk.W, pady=5)

        # --- Seção CRUD (Tabela) ---
        frame_crud = tk.Frame(self.root, bg=WHITE, bd=1, relief=tk.SOLID, padx=15, pady=15)
        # expand=True permite que a tabela cresça, mas a área de edição será preservada
        frame_crud.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        tk.Label(frame_crud, text="Registros Salvos (fascinante.csv)", bg=WHITE, fg=DARK_BLUE, font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))

        # Container interno para a Tabela e as Barras de Rolagem
        frame_tabela = tk.Frame(frame_crud)
        frame_tabela.pack(fill=tk.BOTH, expand=True, pady=10)

        scroll_y = ttk.Scrollbar(frame_tabela, orient=tk.VERTICAL)
        scroll_x = ttk.Scrollbar(frame_tabela, orient=tk.HORIZONTAL)

        colunas = ("Data e Hora", "Assunto", "Link", "Texto Complementar")
        self.tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", selectmode="browse",
                                 yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        
        scroll_y.config(command=self.tree.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scroll_x.config(command=self.tree.xview)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configurando tamanhos fixos para as colunas (stretch=False para ativar scroll horizontal)
        # Assunto, Link e Texto com 600px acomodam confortavelmente 100 caracteres
        self.tree.column("Data e Hora", width=150, anchor=tk.W, stretch=tk.NO)
        self.tree.column("Assunto", width=600, anchor=tk.W, stretch=tk.NO)
        self.tree.column("Link", width=600, anchor=tk.W, stretch=tk.NO)
        self.tree.column("Texto Complementar", width=600, anchor=tk.W, stretch=tk.NO)

        for col in colunas:
            self.tree.heading(col, text=col)

        self.tree.bind("<Double-1>", self.carregar_para_edicao) 

        # --- Área de Edição/Exclusão (Tamanho fixo na parte inferior) ---
        frame_edicao = tk.Frame(frame_crud, bg=LIGHT_BLUE, padx=10, pady=15)
        frame_edicao.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(frame_edicao, text="Selecione um item na tabela com Duplo Clique para Editar/Excluir/Abrir", bg=LIGHT_BLUE, font=('Arial', 9, 'italic')).grid(row=0, column=0, columnspan=5, pady=(0, 10), sticky=tk.W)

        # Entradas
        tk.Label(frame_edicao, text="Assunto:", bg=LIGHT_BLUE).grid(row=1, column=0, sticky=tk.E, padx=5)
        self.entry_assunto = tk.Entry(frame_edicao, width=35)
        self.entry_assunto.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame_edicao, text="Texto Compl.:", bg=LIGHT_BLUE).grid(row=1, column=2, sticky=tk.E, padx=5)
        self.entry_texto = tk.Entry(frame_edicao, width=35)
        self.entry_texto.grid(row=1, column=3, padx=5, pady=5)

        tk.Label(frame_edicao, text="Link:", bg=LIGHT_BLUE).grid(row=2, column=0, sticky=tk.E, padx=5)
        self.entry_link = tk.Entry(frame_edicao, width=35)
        self.entry_link.grid(row=2, column=1, padx=5, pady=5)

        # Botões de Ação na Edição
        frame_botoes = tk.Frame(frame_edicao, bg=LIGHT_BLUE)
        frame_botoes.grid(row=2, column=2, columnspan=2, sticky=tk.W, padx=5)

        btn_atualizar = tk.Button(frame_botoes, text="Atualizar", bg=PRIMARY_BLUE, fg=WHITE, relief=tk.FLAT, command=self.atualizar_registro)
        btn_atualizar.pack(side=tk.LEFT, padx=5)

        btn_excluir = tk.Button(frame_botoes, text="Excluir", bg="#cc0000", fg=WHITE, relief=tk.FLAT, command=self.excluir_registro)
        btn_excluir.pack(side=tk.LEFT, padx=5)

        # Novo botão: Abrir Link
        btn_abrir = tk.Button(frame_botoes, text="Abrir Link", bg=GREEN_BTN, fg=WHITE, relief=tk.FLAT, command=self.abrir_link_navegador)
        btn_abrir.pack(side=tk.LEFT, padx=5)

    # --- Funções CRUD e Lógica ---
    def extrair_dados(self):
        texto = self.text_input.get("1.0", tk.END).strip()
        if not texto:
            messagebox.showwarning("Atenção", "Por favor, cole o texto antes de extrair.")
            return

        assunto_extraido = ""
        link_extraido = ""

        match_assunto = re.search(r'Assista a "(.*?)"', texto, re.IGNORECASE)
        if match_assunto:
            assunto_extraido = match_assunto.group(1)
        else:
            linhas = [l.strip() for l in texto.split('\n') if l.strip()]
            if linhas: assunto_extraido = linhas[0]

        # Lógica de Limpeza do Assunto (Remove hashtags e emojis)
        if assunto_extraido:
            # 1. Remove qualquer hashtag (ex: #shorts, #feed)
            assunto_limpo = re.sub(r'#\S+', '', assunto_extraido)
            # 2. Remove emojis e caracteres indesejados (mantém letras, números, pontuação e acentuação PT-BR)
            assunto_limpo = re.sub(r'[^\w\s.,!?"\'-À-ÿ]', '', assunto_limpo)
            # 3. Limpa espaços duplos e nas bordas
            assunto_extraido = re.sub(r'\s+', ' ', assunto_limpo).strip()

        match_link = re.search(r'(https?://[^\s]+)', texto)
        if match_link:
            link_extraido = match_link.group(1)

        if not assunto_extraido and not link_extraido:
            messagebox.showwarning("Erro", "Não foi possível extrair dados com o padrão esperado.")
            return

        datahora = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        novo_registro = {
            "datahora": datahora,
            "assunto": assunto_extraido,
            "link": link_extraido,
            "texto_complementar": ""
        }

        self.registros.append(novo_registro)
        self.salvar_csv()
        self.renderizar_tabela()
        self.text_input.delete("1.0", tk.END)

    def renderizar_tabela(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i, r in enumerate(self.registros):
            self.tree.insert("", tk.END, iid=i, values=(r["datahora"], r["assunto"], r["link"], r["texto_complementar"]))

    def carregar_para_edicao(self, event):
        selecionado = self.tree.selection()
        if selecionado:
            index = int(selecionado[0])
            registro = self.registros[index]
            
            self.entry_assunto.delete(0, tk.END)
            self.entry_assunto.insert(0, registro["assunto"])
            
            self.entry_link.delete(0, tk.END)
            self.entry_link.insert(0, registro["link"])
            
            self.entry_texto.delete(0, tk.END)
            self.entry_texto.insert(0, registro["texto_complementar"])
            
            self.indice_edicao = index

    def atualizar_registro(self):
        if hasattr(self, 'indice_edicao'):
            i = self.indice_edicao
            self.registros[i]["assunto"] = self.entry_assunto.get()
            self.registros[i]["link"] = self.entry_link.get()
            self.registros[i]["texto_complementar"] = self.entry_texto.get()
            
            self.salvar_csv()
            self.renderizar_tabela()
            self.limpar_campos_edicao()

    def excluir_registro(self):
        if hasattr(self, 'indice_edicao'):
            if messagebox.askyesno("Confirmar", "Deseja realmente excluir este registro?"):
                del self.registros[self.indice_edicao]
                self.salvar_csv()
                self.renderizar_tabela()
                self.limpar_campos_edicao()

    def abrir_link_navegador(self):
        """Abre o link que estiver atualmente no campo de edição no navegador padrão."""
        link = self.entry_link.get().strip()
        if link and link.startswith("http"):
            webbrowser.open(link)
        else:
            messagebox.showinfo("Aviso", "Não há um link válido preenchido para abrir. Selecione um item na tabela primeiro.")

    def limpar_campos_edicao(self):
        self.entry_assunto.delete(0, tk.END)
        self.entry_link.delete(0, tk.END)
        self.entry_texto.delete(0, tk.END)
        if hasattr(self, 'indice_edicao'):
            delattr(self, 'indice_edicao')

    def carregar_csv(self):
        self.registros = []
        if os.path.exists(self.csv_path):
            with open(self.csv_path, mode='r', encoding='utf-8') as f:
                leitor = csv.DictReader(f, delimiter=';')
                for linha in leitor:
                    self.registros.append(linha)
        self.renderizar_tabela()

    def salvar_csv(self):
        campos = ["datahora", "assunto", "link", "texto_complementar"]
        with open(self.csv_path, mode='w', newline='', encoding='utf-8') as f:
            escritor = csv.DictWriter(f, fieldnames=campos, delimiter=';')
            escritor.writeheader()
            escritor.writerows(self.registros)

    def on_closing(self):
        try:
            print("Executando Git Push automático...")
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            subprocess.run(["git", "commit", "-m", f"Atualização via App em {data_hora}"], cwd=self.repo_path, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            subprocess.run(["git", "push"], cwd=self.repo_path, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            
            messagebox.showinfo("Git Push", "Dados salvos e sincronizados com o GitHub com sucesso!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erro Git", f"Falha ao enviar para o repositório.\nDetalhes: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n{e}")
        finally:
            self.root.destroy()


# ==========================================
# FUNÇÕES DE INICIALIZAÇÃO E GIT PULL
# ==========================================
def obter_diretorio_repo():
    config_file = 'config.json'
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                pasta = config.get('repo_path')
                if pasta and os.path.exists(pasta):
                    return pasta
        except:
            pass

    messagebox.showinfo("Configuração Inicial", "Por favor, selecione a pasta onde está o repositório git 'fascinante'.\n\nEssa ação só será necessária na primeira vez.")
    pasta_escolhida = filedialog.askdirectory(title="Selecione a pasta do repositório")
    
    if pasta_escolhida:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump({'repo_path': pasta_escolhida}, f)
        return pasta_escolhida
    return None

def executar_git_pull(repo_path):
    print("Sincronizando com o GitHub (Git Pull)...")
    try:
        subprocess.run(["git", "pull"], cwd=repo_path, capture_output=True, text=True, check=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        print("Git Pull bem sucedido!")
    except subprocess.CalledProcessError as e:
        messagebox.showwarning("Aviso Git Pull", f"O 'git pull' falhou. Você pode estar offline ou há conflitos.\nO aplicativo abrirá mesmo assim.\n\nDetalhes:\n{e.stderr}")
    except FileNotFoundError:
         messagebox.showerror("Erro", "Comando 'git' não encontrado. Verifique se o Git está instalado nas variáveis de ambiente do sistema.")

# ==========================================
# BOOTSTRAP DA APLICAÇÃO
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw() 
    
    repo_path = obter_diretorio_repo()
    
    if not repo_path:
        messagebox.showerror("Cancelado", "A pasta do repositório é obrigatória para executar o sistema.")
        root.destroy()
    else:
        executar_git_pull(repo_path)
        root.deiconify() 
        app = AppFascinante(root, repo_path)
        root.mainloop()