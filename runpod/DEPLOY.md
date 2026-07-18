# Redeploy RunPod Whisper (alta precisión)

## Urgente: `worker sin handler activo` / output vacío (~55ms)

Si en Railway ves:

```
RunPod: worker sin handler activo (55ms). Redeploy imagen whisper-runpod.
Request failed with status code 502
```

**Causa habitual A:** el backend envía `quality: "max"` o `url` al worker del **Hub Faster Whisper**. Ese schema no los acepta → job `COMPLETED` en ~50ms **sin output**. El backend ya manda el payload oficial (`audio`, `model`, `transcription`, …).

**Causa habitual B:** imagen Docker incorrecta en el endpoint. El Hub usa `registry.runpod.net/runpod-workers-worker-faster-whisper-...`. La imagen custom `mikeshinoda26/whisper-runpod:latest` requiere `RUNPOD_USE_CUSTOM_IMAGE=true` en Railway (no uses `RUNPOD_WHISPER_HANDLER=custom` con el Hub).

**También:** en Logs del endpoint, si ves `Failed to return job results | 400 ... job-done`, el worker **sí procesó** el audio pero el SDK RunPod viejo (`1.7.9`) no pudo devolver el resultado. Rebuild con `runpod==1.9.1` (ver abajo) y esperá rollout **3/3 workers**.

**Verificar:**

```bash
curl -s -X POST "https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input":{"ping":true}}'
```

Debe incluir `"output":{"pong":true,...}`. Si solo ves `"status":"COMPLETED"` sin `output`, el worker está roto.

**Solución (5 min):**

1. GitHub → **Actions** → **Build RunPod Whisper Image** → **Run workflow**
2. [console.runpod.io/serverless](https://console.runpod.io/serverless) → endpoint `k5unvhyq15o65y`
3. **Edit** → Docker image: `mikeshinoda26/whisper-runpod:latest` → **Save & redeploy**
4. Volver a probar el `curl` ping hasta ver `"pong":true`
5. Reprocesar la transcripción en la app

---

Si ves `job completado pero output vacío` con `executionTime` ~21ms, el worker **no está ejecutando el handler**. Hay que rebuild + push de la imagen y actualizar el endpoint.

## Calidad de transcripción

La imagen usa **Whisper large-v3** con decodificación de máxima precisión:

| Parámetro | Valor | Efecto |
|-----------|-------|--------|
| `WHISPER_MODEL` | `large-v3` | Mejor modelo disponible |
| `WHISPER_BEAM_SIZE` | `10` | Beam search amplio |
| `WHISPER_BEST_OF` | `5` | Más candidatos |
| `WHISPER_PATIENCE` | `2.0` | Beam más exhaustivo |
| `WHISPER_VAD` | `true` | Solo imagen Docker propia. En el Hub, el backend manda `enable_vad: false` por defecto |
| `temperature` | `[0.0]` | Solo decodificación determinista |

Variables opcionales en el endpoint RunPod (Environment):

```
WHISPER_MODEL=large-v3
WHISPER_DEVICE=cuda
WHISPER_COMPUTE=float16
WHISPER_BEAM_SIZE=10
WHISPER_BEST_OF=5
WHISPER_PATIENCE=2.0
WHISPER_VAD=true
WHISPER_REPETITION_PENALTY=1.05
```

**Nota:** 99,99% de precisión depende también del audio (ruido, micrófono, compresión). Los videos ahora se transcriben desde el archivo **original** en R2, no desde el MP3 de 32kbps de reproducción.

## 1. Build y push (GitHub Actions)

Repo → **Actions** → **Build RunPod Whisper Image** → **Run workflow**

Imagen: `mikeshinoda26/whisper-runpod:latest`

## 2. Actualizar endpoint en RunPod

1. [console.runpod.io/serverless](https://console.runpod.io/serverless) → endpoint `k5unvhyq15o65y`
2. **Edit** → Docker image: `mikeshinoda26/whisper-runpod:latest`
3. Agregar variables de entorno (tabla arriba)
4. **Redeploy** / reiniciar workers

## 3. Verificar

```bash
curl -X POST "https://api.runpod.ai/v2/$RUNPOD_ENDPOINT_ID/runsync" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input":{"ping":true}}'
```

Debe devolver `"output":{"pong":true,"quality":"max",...}` (no `output` vacío).

## 4. Backend (Railway)

Después de merge, redeploy del servicio **Backend** para aplicar:

- Videos: transcripción desde `r2Key` original (no MP3 de reproducción)
- Fallback local: compresión a 128kbps mono para Whisper
