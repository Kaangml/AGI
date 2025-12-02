"""Router için basit API fonksiyonları"""

from .classifier import classify, get_classifier, route


def route_message(text: str) -> str:
    """
    Mesajı yönlendir ve adapter ID döndür.
    
    Args:
        text: Kullanıcı mesajı
        
    Returns:
        adapter_id: Kullanılacak adapter'ın ID'si
    """
    return route(text)


def route_with_details(text: str) -> dict:
    """
    Mesajı yönlendir ve detaylı bilgi döndür.
    
    Args:
        text: Kullanıcı mesajı
        
    Returns:
        {
            "adapter_id": str,
            "intent": str,
            "confidence": float,
            "all_scores": dict
        }
    """
    return classify(text)


def get_router_info() -> dict:
    """Router hakkında bilgi döndür"""
    return get_classifier().get_stats()


__all__ = ["route_message", "route_with_details", "get_router_info"]
