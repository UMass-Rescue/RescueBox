poetry run pip install --upgrade torch torchvision --index-url https://download.pytorch.org/whl/cu130 > /dev/null 2>&1

RC=`poetry run python -c "import torch; print(torch.cuda.is_available())"`

echo ""
if [[ "$RC" == "True" ]]; then
    echo "==============================="
    echo "torch for CLIP will use GPU"
    echo "==============================="
else
   echo "torch for CLIP will not use gpu , CPU only"
fi


