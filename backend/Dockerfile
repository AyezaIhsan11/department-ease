FROM python:3.9

# Create a non-root user (UID 1000) for Hugging Face Spaces
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

# Copy requirements and install dependencies
COPY --chown=user:user ./requirements.txt $HOME/app/requirements.txt
RUN pip install --no-cache-dir --user --upgrade -r $HOME/app/requirements.txt

# Copy all code
COPY --chown=user:user . $HOME/app

# Start the application on port 7860
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
