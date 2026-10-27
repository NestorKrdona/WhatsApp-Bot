"""
Ejecuta el Caso de prueba 2 (Punto 3) usando GARAK de verdad: importa y corre su CLI
oficial (python -m garak) con el generator personalizado whatsapp_generator.py, que
conecta cada sonda de Garak con el canal de WhatsApp de pruebas real.

A diferencia de run_case2_injection.py (un script propio con 3 mensajes curados a
mano, que NO usa Garak), este script si invoca el motor de Garak: sus probes
(promptinject, dan, leakreplay, etc.), sus detectores, y su sistema de reportes
oficial (.report.jsonl y .report.html). Ver:
  https://docs.garak.ai/garak/examples/basic-test
  https://docs.garak.ai/garak/examples/prompt-injection

Requiere:
  pip install garak
  Haber escaneado el QR de WhatsApp Web con el numero de pruebas "Estudiante"
  (CASE2_STUDENT_NUMBER / WHATSAPP_TEST_NUMBER), NO el numero no registrado.

Variables de entorno:
  AGENT_TEST_NUMBER / WHATSAPP_AGENT_NUMBER  numero del canal de pruebas del agente (DESTINO)
  WHATSAPP_TEST_NUMBER                       numero de pruebas "Estudiante" ya autenticado
  WHATSAPP_BOT_WS_URL                        opcional, por defecto ws://localhost:3060
  GARAK_PROBES                               opcional, lista separada por comas de TODAS las
                                              sondas a correr
                                              (por defecto: promptinject.HijackHateHumans,dan.DAN_Jailbreak,leakreplay.GuardianCloze
                                              - nombres verificados contra garak 0.17.1 con
                                              `python -m garak --list_probes`; revisar si
                                              cambian en otra version)
  GARAK_SCALED_PROBES                        opcional, lista separada por comas de las sondas
                                              que AUTOESCALAN su cantidad de prompts (se
                                              limitan con GARAK_PROMPT_CAP y se corren con
                                              generations=1 para que el total de intentos sea
                                              exactamente el cap, sin multiplicarse)
                                              (por defecto: promptinject.HijackHateHumans)
  GARAK_PROMPT_CAP                           opcional, limite de prompts distintos para las
                                              sondas de GARAK_SCALED_PROBES (run.soft_probe_
                                              prompt_cap de garak; su valor por defecto en
                                              garak es 256, que es lo que produjo los 256
                                              prompts de promptinject.HijackHateHumans en la
                                              primera corrida). Aqui el default es 30. Estas
                                              sondas se corren SIEMPRE con generations=1, asi
                                              que 30 intentos de cap = 30 intentos reales
                                              (no 30 x GARAK_GENERATIONS).
  GARAK_GENERATIONS                          opcional, cuantas veces repetir cada prompt de
                                              las sondas de conteo FIJO (todas las que no
                                              estan en GARAK_SCALED_PROBES, p.ej.
                                              dan.DAN_Jailbreak y leakreplay.GuardianCloze)
                                              (por defecto 3; Garak por defecto usa 10, pero
                                              aqui cada repeticion es un mensaje real de
                                              WhatsApp con espera de respuesta, no una
                                              llamada de API instantanea)

Uso:
  export AGENT_TEST_NUMBER="573042675682"
  export WHATSAPP_TEST_NUMBER="573182271073"
  python garak_integration/run_case2_garak.py

Este script es un wrapper de conveniencia: arma el/los comando(s), los corre, y copia
los reportes de Garak a garak_integration/results/ para que queden junto a los demas
resultados del Punto 3. Si hay sondas en ambos grupos (escaladas y de conteo fijo), se
hacen DOS corridas de garak (cada una con su propio run_uuid y su propio reporte),
porque --generations es un parametro global de la corrida y no se puede fijar distinto
por sonda en una sola invocacion de la CLI. El comando de la corrida "escalada" equivale a:

  PYTHONPATH=. python -m garak --config <cap.yaml> \
      --model_type whatsapp_generator.WhatsAppGenerator \
      --model_name "$WHATSAPP_TEST_NUMBER" \
      --probes promptinject.HijackHateHumans \
      --generations 1
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")
GARAK_RUNS_DIR = os.path.expanduser("~/.local/share/garak/garak_runs")


def check_garak_installed():
    try:
        import garak  # noqa: F401
        return True
    except ImportError:
        return False


def install_generator_into_garak():
    """Copia whatsapp_generator.py dentro de garak/generators/ del propio paquete
    instalado de garak. Es necesario porque el cargador de plugins de garak solo
    importa generators como submodulos de garak.generators.* (import_module("garak."
    + categoria + "." + nombre)); no soporta apuntar a un modulo externo via
    PYTHONPATH como se asumia originalmente. Se sobre-escribe en cada corrida para
    que quede siempre sincronizado con el codigo de este repositorio."""
    import garak
    generators_dir = os.path.join(os.path.dirname(garak.__file__), "generators")
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whatsapp_generator.py")
    dest = os.path.join(generators_dir, "whatsapp_generator.py")
    shutil.copy2(src, dest)
    print(f"Generator instalado en: {dest}")
    return dest


def run_garak_once(label, probes_csv, generations, env, extra_config_lines=None):
    """Corre una invocacion de `python -m garak` para el grupo de sondas dado y
    copia los reportes nuevos a results/. Devuelve la lista de archivos copiados."""
    config_path = None
    cmd = [
        sys.executable, "-m", "garak",
        "--model_type", "whatsapp_generator.WhatsAppGenerator",
        "--model_name", env["WHATSAPP_TEST_NUMBER"],
        "--probes", probes_csv,
        "--generations", str(generations),
    ]
    if extra_config_lines:
        config_fd, config_path = tempfile.mkstemp(suffix=".yaml", prefix="garak_cfg_")
        with os.fdopen(config_fd, "w") as f:
            f.write("---\n" + extra_config_lines)
        cmd[3:3] = ["--config", config_path]

    print(f"\n=== Corrida '{label}': probes=[{probes_csv}] generations={generations} ===")
    if config_path:
        print(f"(config temporal: {config_path})")
    print("Ejecutando:", " ".join(cmd))

    before = set(glob.glob(os.path.join(GARAK_RUNS_DIR, "*")))
    result = subprocess.run(cmd, cwd=REPO_ROOT, env=env)
    after = set(glob.glob(os.path.join(GARAK_RUNS_DIR, "*")))
    new_files = sorted(after - before, key=os.path.getmtime)

    if result.returncode != 0:
        print(f"\ngarak ('{label}') termino con codigo de salida {result.returncode}. Revisa la salida de arriba.")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    copied = []
    for f in new_files:
        dest = os.path.join(RESULTS_DIR, os.path.basename(f))
        shutil.copy2(f, dest)
        copied.append(dest)
    return copied


def run():
    agent_number = os.environ.get("AGENT_TEST_NUMBER") or os.environ.get("WHATSAPP_AGENT_NUMBER")
    student_number = os.environ.get("WHATSAPP_TEST_NUMBER")
    if not agent_number or not student_number:
        print(
            "Debes definir AGENT_TEST_NUMBER (o WHATSAPP_AGENT_NUMBER) y "
            "WHATSAPP_TEST_NUMBER como variables de entorno antes de ejecutar este script."
        )
        sys.exit(1)

    if not check_garak_installed():
        print("Garak no esta instalado en este entorno. Instalalo con:\n  pip install garak")
        sys.exit(1)

    install_generator_into_garak()

    all_probes = [
        p.strip() for p in os.environ.get(
            "GARAK_PROBES",
            "promptinject.HijackHateHumans,dan.DAN_Jailbreak,leakreplay.GuardianCloze",
        ).split(",") if p.strip()
    ]
    scaled_probes = [
        p.strip() for p in os.environ.get(
            "GARAK_SCALED_PROBES", "promptinject.HijackHateHumans"
        ).split(",") if p.strip()
    ]
    scaled_set = set(scaled_probes)

    scaled_in_run = [p for p in all_probes if p in scaled_set]
    fixed_in_run = [p for p in all_probes if p not in scaled_set]

    prompt_cap = int(os.environ.get("GARAK_PROMPT_CAP", "30"))
    generations = os.environ.get("GARAK_GENERATIONS", "3")

    print(
        f"IMPORTANTE: este comando envia las sondas de Garak AL numero {agent_number} "
        f"(canal de pruebas del agente). El REMITENTE real es quien escaneo el QR en "
        f"la sesion de WhatsApp Web del bot: asegurate de que sea el telefono de "
        f"{student_number} (el numero 'Estudiante') antes de continuar.\n"
    )
    print(
        f"Sondas escaladas (cap={prompt_cap}, generations=1 -> {prompt_cap} intentos reales c/u): "
        f"{scaled_in_run or '(ninguna)'}"
    )
    print(
        f"Sondas de conteo fijo (generations={generations}): {fixed_in_run or '(ninguna)'}"
    )

    env = os.environ.copy()
    env["WHATSAPP_AGENT_NUMBER"] = agent_number
    env["WHATSAPP_TEST_NUMBER"] = student_number
    # Garak espera --model_type en formato "modulo.Clase" con "modulo" de UN SOLO
    # nivel (sin puntos); al anteponer internamente "generators." debe quedar en
    # exactamente 3 partes (categoria.modulo.clase). Por eso se agrega la carpeta
    # garak_integration/ directamente al PYTHONPATH, para poder importar
    # "whatsapp_generator" como modulo plano (ademas de REPO_ROOT, que sigue
    # haciendo falta para que whatsapp_generator.py pueda hacer
    # "from garak_integration.whatsapp_ws_client import ...").
    GARAK_INTEGRATION_DIR = os.path.join(REPO_ROOT, "garak_integration")
    env["PYTHONPATH"] = os.pathsep.join(
        [REPO_ROOT, GARAK_INTEGRATION_DIR, env.get("PYTHONPATH", "")]
    )

    all_copied = []

    if scaled_in_run:
        # generations=1 a proposito: el cap ya define el total de prompts distintos;
        # repetirlos con generations>1 multiplicaria el total por encima del cap
        # (por ejemplo cap=30 x generations=3 = 90 intentos, que es justo lo que se
        # quiere evitar).
        all_copied += run_garak_once(
            label="sondas escaladas",
            probes_csv=",".join(scaled_in_run),
            generations=1,
            env=env,
            extra_config_lines=f"run:\n    soft_probe_prompt_cap: {prompt_cap}\n",
        )

    if fixed_in_run:
        all_copied += run_garak_once(
            label="sondas de conteo fijo",
            probes_csv=",".join(fixed_in_run),
            generations=generations,
            env=env,
        )

    if all_copied:
        print("\nReporte(s) de Garak copiados a garak_integration/results/:")
        for c in all_copied:
            print(f"  {c}")
        print(
            "\nCada .report.jsonl/.report.html es el reporte oficial de Garak de una de "
            "las dos corridas (probes, detectores y tasa de fallo por sonda). Si hubo dos "
            "corridas, cada una tiene su propio run_uuid; referenciar ambas como evidencia "
            "de ejecucion en el Punto 3 (Caso de prueba 2)."
        )
    else:
        print(
            f"\nNo se detectaron reportes nuevos en {GARAK_RUNS_DIR}. "
            "Revisa si garak corrio correctamente arriba."
        )


if __name__ == "__main__":
    run()
