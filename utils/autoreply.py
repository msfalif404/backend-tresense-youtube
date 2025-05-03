from core.config import model

def generate_reply_with_gemini(prompt: str) -> str:
    response = model.generate_content(
        f"""
        You are a Youtube AI Agent Generator. Generate a comment for the following video comment: {prompt}
        The comment should be in Indonesian language. The comment should be a reply to the original comment.
        The comment should be a positive comment. The comment should be a short comment. The comment should be a funny comment.
        """
    ).text
    return response

def generate_sentiment_with_gemini(prompt: str) -> str:
    response = model.generate_content(
        f"""
        You are a Youtube AI Agent Generator. Generate a sentiment for the following video comment: {prompt}
        The sentiment should be selected from the following options: `positive`, `negative`, `neutral`.
        You just answer with the sentiment only without any explanation.
        """
    ).text
    return response