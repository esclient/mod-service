from modservice.repository.repository import ModRepository


def confirm_upload(repo: ModRepository, mod_id: int) -> bool:
    """
    Confirm that a mod has been successfully uploaded by updating its status.
    
    Args:
        repo: Repository instance
        mod_id: ID of the mod to confirm
        
    Returns:
        bool: True if successfully confirmed, False otherwise
    """
    return repo.confirm_upload(mod_id)
