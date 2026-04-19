import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
import json
import subprocess
from datetime import datetime
import re

# ==========================================
# CONFIGURAÇÕES DE CORES (Baseado no CSS)
# ==========================================
BG_COLOR = "#f4f7f6"
WHITE = "#ffffff"
PRIMARY_BLUE = "#0066cc"
DARK_BLUE = "#004080"
LIGHT_BLUE = "#e6f0ff"
TEXT_COLOR = "#333333"

# ==========================================
# LÓGICA PRINCIPAL DO APLICATIVO
# ==========================================
class AppFascinante:
    def __init__(self, root, repo_path):
        self.root = root
        self.repo_path = repo_path
        self.csv_path = os.path.join(repo_path, 'fascinante.csv')
        self.registros = []

        # Configurações da Janela Principal
        self.root.title("Extrator e Gerenciador - Projeto Fascinante")
        self.root.geometry("900x700")
        self.root.configure(bg=BG_COLOR)
        
        # Intercepta o fechamento da janela (no "X") para executar o Git Push
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.setup_ui()
        self.carregar_csv()

    def setup_ui(self):
        # --- Estilização do ttk ---
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
        frame_crud.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        tk.Label(frame_crud, text="Registros Salvos (fascinante.csv)", bg=WHITE, fg=DARK_BLUE, font=('Arial', 12, 'bold')).pack(anchor=tk.W, pady=(0, 5))

        # Tabela (Treeview)
        colunas = ("Data e Hora", "Assunto", "Link", "Texto Complementar")
        self.tree = ttk.Treeview(frame_crud, columns=colunas, show="headings", selectmode="browse")
        for col in colunas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor=tk.W)
        
        self.tree.pack(fill=tk.BOTH, expand=True, pady=10)
        self.tree.bind("<Double-1>", self.carregar_para_edicao) # Duplo clique para editar

        # --- Área de Edição/Exclusão ---
        frame_edicao = tk.Frame(frame_crud, bg=LIGHT_BLUE, padx=10, pady=10)
        frame_edicao.pack(fill=tk.X)

        tk.Label(frame_edicao, text="Selecione um item na tabela com Duplo Clique para Editar/Excluir", bg=LIGHT_BLUE, font=('Arial', 9, 'italic')).grid(row=0, column=0, columnspan=4, pady=5, sticky=tk.W)

        # Entradas para edição
        tk.Label(frame_edicao, text="Assunto:", bg=LIGHT_BLUE).grid(row=1, column=0, sticky=tk.E, padx=5)
        self.entry_assunto = tk.Entry(frame_edicao, width=30)
        self.entry_assunto.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame_edicao, text="Texto Compl.:", bg=LIGHT_BLUE).grid(row=1, column=2, sticky=tk.E, padx=5)
        self.entry_texto = tk.Entry(frame_edicao, width=30)
        self.entry_texto.grid(row=1, column=3, padx=5, pady=5)

        tk.Label(frame_edicao, text="Link:", bg=LIGHT_BLUE).grid(row=2, column=0, sticky=tk.E, padx=5)
        self.entry_link = tk.Entry(frame_edicao, width=30)
        self.entry_link.grid(row=2, column=1, padx=5, pady=5)

        # Botões de Ação
        frame_botoes = tk.Frame(frame_edicao, bg=LIGHT_BLUE)
        frame_botoes.grid(row=2, column=2, columnspan=2, sticky=tk.W, padx=5)

        btn_atualizar = tk.Button(frame_botoes, text="Atualizar", bg=PRIMARY_BLUE, fg=WHITE, relief=tk.FLAT, command=self.atualizar_registro)
        btn_atualizar.pack(side=tk.LEFT, padx=5)

        btn_excluir = tk.Button(frame_botoes, text="Excluir", bg="#cc0000", fg=WHITE, relief=tk.FLAT, command=self.excluir_registro)
        btn_excluir.pack(side=tk.LEFT, padx=5)

    # --- Funções CRUD e Lógica ---
    def extrair_dados(self):
        texto = self.text_input.get("1.0", tk.END).strip()
        if not texto:
            messagebox.showwarning("Atenção", "Por favor, cole o texto antes de extrair.")
            return

        assunto_extraido = ""
        link_extraido = ""

        # Regex similar ao do Javascript
        match_assunto = re.search(r'Assista a "(.*?)"', texto, re.IGNORECASE)
        if match_assunto:
            assunto_extraido = match_assunto.group(1)
        else:
            linhas = [l.strip() for l in texto.split('\n') if l.strip()]
            if linhas: assunto_extraido = linhas[0]

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
        messagebox.showinfo("Sucesso", "Dados extraídos e salvos com sucesso!")

    def renderizar_tabela(self):
        # Limpa a tabela atual
        for item in self.tree.get_children():
            self.tree.delete(item)
        # Preenche com os dados
        for i, r in enumerate(self.registros):
            self.tree.insert("", tk.END, iid=i, values=(r["datahora"], r["assunto"], r["link"], r["texto_complementar"]))

    def carregar_para_edicao(self, event):
        selecionado = self.tree.selection()
        if selecionado:
            index = int(selecionado[0])
            registro = self.registros[index]
            
            # Limpa e preenche as entradas
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

    def limpar_campos_edicao(self):
        self.entry_assunto.delete(0, tk.END)
        self.entry_link.delete(0, tk.END)
        self.entry_texto.delete(0, tk.END)
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
        """Executado ao fechar o programa: Adiciona, Commita e faz Push pro Git."""
        try:
            print("Executando Git Push automático...")
            data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Executa git add .
            subprocess.run(["git", "add", "."], cwd=self.repo_path, check=True)
            
            # Executa git commit (se não houver alterações, isso gera erro que ignoramos silenciosamente)
            subprocess.run(["git", "commit", "-m", f"Atualização via App em {data_hora}"], cwd=self.repo_path)
            
            # Executa git push
            subprocess.run(["git", "push"], cwd=self.repo_path, check=True)
            
            messagebox.showinfo("Git Push", "Dados salvos e sincronizados com o GitHub com sucesso!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Erro Git", f"Falha ao enviar para o repositório.\nDetalhes: {e}")
        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro inesperado:\n{e}")
        finally:
            self.root.destroy() # Fecha a janela


# ==========================================
# FUNÇÕES DE INICIALIZAÇÃO E GIT PULL
# ==========================================
def obter_diretorio_repo():
    config_file = 'config.json'
    
    # Tenta carregar do arquivo
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                pasta = config.get('repo_path')
                if pasta and os.path.exists(pasta):
                    return pasta
        except:
            pass # Se der erro ao ler, pede a pasta novamente

    # Pede ao usuário se não encontrar a configuração
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
        resultado = subprocess.run(["git", "pull"], cwd=repo_path, capture_output=True, text=True, check=True)
        print("Git Pull bem sucedido!")
    except subprocess.CalledProcessError as e:
        messagebox.showwarning("Aviso Git Pull", f"O 'git pull' falhou. Você pode estar offline ou há conflitos.\nO aplicativo abrirá mesmo assim.\n\nDetalhes:\n{e.stderr}")
    except FileNotFoundError:
         messagebox.showerror("Erro", "Comando 'git' não encontrado. Verifique se o Git está instalado nas variáveis de ambiente do sistema.")


# ==========================================
# BOOTSTRAP DA APLICAÇÃO
# ==========================================
if __name__ == "__main__":
    # Cria a raiz oculta para os diálogos iniciais
    root = tk.Tk()
    root.withdraw() 
    
    # 1. Pede ou lê a pasta do repositório
    repo_path = obter_diretorio_repo()
    
    if not repo_path:
        messagebox.showerror("Cancelado", "A pasta do repositório é obrigatória para executar o sistema.")
        root.destroy()
    else:
        # 2. Executa o git pull antes de qualquer coisa
        executar_git_pull(repo_path)
        
        # 3. Abre a interface do aplicativo
        root.deiconify() # Mostra a janela novamente
        app = AppFascinante(root, repo_path)
        root.mainloop()