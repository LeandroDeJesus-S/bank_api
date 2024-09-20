# API de banco assíncrona
API bancária assíncrona usando Fast API.

---
### Workflow
[x] Gerenciamento de usuários como criação, listagem, atualização e exclusão.

[x] Gerenciamento de contas e tipos de conta.

[x] Uso roles para controle de permissões.

[x] Cadastro de transações como depósitos, saques e transferências.

[x] Exibição de extrato de uma ou todas as contas mostrando todas as transações realizadas.

[x] Utilização de Json Web Tokens para realizar a autenticação e autorização.

[x] Gerenciamento de migrações do banco de dados com `alembic`.

[ ] remoção do package `databases` para uso do sqlalchemy assíncrono nativo.

---
### Pré-requirements
- [Python](https://python.org/downloads/)
- [Poetry](https://python-poetry.org/docs/#installation)

---
### Quick start
1. Clone este repositório.
   ```shell
   git clone https://github.com/LeandroDeJesus-S/bank_api.git
   ```

2. Entre no diretório do projeto.
   ```shell
   cd bank_api/
   ```

3. Instale as dependências.
   ```shell
   poetry install
   ```

4. Crie e configure um arquivo `.env` seguindo o arquivo de exemplo `.env-example`.

5. Execute os testes.
   ```shell
   poetry run pytest
   ```

6. Faça as migrações
   ```
   poetry run alembic upgrade head
   ```

7. Execute a aplicação.
   ```shell
   poetry run uvicorn main:api
   ```

8. Faça o teste.
   ```shell
   # usando httpie
   http POST /users/ username=usr password=Password@123 first_name=name last_name=surname cpf="187.763.740-84" birthdate='2004-03-21'
   ```
   ou acesse http://localhost:8000/docs pelo navegador para ter acesso a interface do swagger.
