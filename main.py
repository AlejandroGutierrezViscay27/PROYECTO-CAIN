import sys
from dotenv import load_dotenv

load_dotenv()

def modo_terminal():
    from core.agent import Cain
    agent = Cain()
    print("🎪 CAIN ha iniciado — Modo Terminal")
    print("Escribe 'salir' para terminar.\n")
    while True:
        usuario = input("TÚ: ")
        if usuario.lower() == "salir":
            print("🎪 CAIN: El espectáculo termina... por ahora.")
            break
        print(f"\nCAIN: {agent.chat(usuario)}\n")

def modo_web():
    import uvicorn
    print("🎪 CAIN ha iniciado — Modo Web")
    print("Abre http://localhost:8000 en tu navegador\n")
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=False)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "terminal":
        modo_terminal()
    else:
        modo_web()