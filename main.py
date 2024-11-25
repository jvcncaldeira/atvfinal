from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

app = FastAPI()

# Modelo para validação dos dados do cliente
class Cliente(BaseModel):
    nome: str = Field(..., max_length=20)
    tipo_atendimento: str = Field(..., min_length=1, max_length=1)
    posicao: int
    data_chegada: datetime
    atendido: bool = False

    @classmethod
    def validar_tipo_atendimento(cls, v):
        if v not in ['N', 'P']:
            raise ValueError('Tipo de atendimento deve ser N (Normal) ou P (Prioritário)')
        return v

# Modelo para receber dados do POST
class ClienteInput(BaseModel):
    nome: str = Field(..., max_length=20)
    tipo_atendimento: str = Field(..., min_length=1, max_length=1)

# Lista para armazenar os clientes (simulando um banco de dados)
fila: List[Cliente] = []

@app.get("/")
async def root():
    return {"message": "API de Fila funcionando!"}

@app.get("/fila", response_model=List[dict])
async def listar_fila():
    """Retorna todos os clientes não atendidos na fila"""
    return [
        {
            "posicao": cliente.posicao,
            "nome": cliente.nome,
            "data_chegada": cliente.data_chegada
        }
        for cliente in fila
        if not cliente.atendido
    ]

@app.get("/fila/{id}")
async def obter_cliente(id: int):
    """Retorna o cliente na posição especificada"""
    for cliente in fila:
        if cliente.posicao == id and not cliente.atendido:
            return {
                "posicao": cliente.posicao,
                "nome": cliente.nome,
                "data_chegada": cliente.data_chegada
            }
    raise HTTPException(status_code=404, detail="Cliente não encontrado na posição especificada")

@app.post("/fila", status_code=201)
async def adicionar_cliente(cliente_input: ClienteInput):
    """Adiciona um novo cliente à fila"""
    # Determina a posição do novo cliente
    posicao = len([c for c in fila if not c.atendido]) + 1
    
    # Cria o novo cliente
    novo_cliente = Cliente(
        nome=cliente_input.nome,
        tipo_atendimento=cliente_input.tipo_atendimento,
        posicao=posicao,
        data_chegada=datetime.now(),
        atendido=False
    )

    # Se for atendimento prioritário, insere na frente dos normais
    if novo_cliente.tipo_atendimento == 'P':
        # Encontra a última posição prioritária
        ultima_pos_prioritaria = 0
        for c in fila:
            if not c.atendido and c.tipo_atendimento == 'P':
                ultima_pos_prioritaria = c.posicao
        
        # Reposiciona os clientes normais
        for c in fila:
            if not c.atendido and c.posicao > ultima_pos_prioritaria:
                c.posicao += 1
        
        novo_cliente.posicao = ultima_pos_prioritaria + 1
    
    fila.append(novo_cliente)
    return {"mensagem": "Cliente adicionado com sucesso", "posicao": novo_cliente.posicao}

@app.put("/fila")
async def atualizar_fila():
    """Atualiza a posição dos clientes na fila"""
    for cliente in fila:
        if not cliente.atendido:
            if cliente.posicao == 1:
                cliente.posicao = 0
                cliente.atendido = True
            else:
                cliente.posicao -= 1
    return {"mensagem": "Fila atualizada com sucesso"}

@app.delete("/fila/{id}")
async def remover_cliente(id: int):
    """Remove um cliente da fila"""
    for i, cliente in enumerate(fila):
        if cliente.posicao == id and not cliente.atendido:
            # Remove o cliente
            fila.pop(i)
            # Atualiza as posições dos clientes restantes
            for c in fila:
                if not c.atendido and c.posicao > id:
                    c.posicao -= 1
            return {"mensagem": "Cliente removido com sucesso"}
    
    raise HTTPException(status_code=404, detail="Cliente não encontrado na posição especificada")
