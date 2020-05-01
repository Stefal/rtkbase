import requests


def check_update(source_url = None, current_release = None, prerelease=True, emit = True):
    """
        check if an update exists
    """
    new_release = {}
    source_url = source_url if source_url is not None else "https://api.github.com/repos/stefal/rtkbase/releases"
    current_release = current_release if current_release is not None else rtkbaseconfig.get("general", "version").strip("v").strip('alpha').strip('beta')
    
    try:    
        response = requests.get(source_url)
        response = r.json()
        for release in response:
            if release.get("prerelease") == prerelease:
                latest_release = release["tag_name"].strip("v").strip('alpha').strip('beta')
                if latest_release > current_release:
                    new_release = {"new_release" : latest_release, "url" : release.get("tarball_url")}
                break
             
    except Exception as e:
        print("Check update error: ", e)
        
    return new_release

def update_rtkbase():
    """
        download and update rtkbase
    """
    #Check if an update is available
    update_url = check_update(emit=False).get("url")
    if update_url is None:
        return

    import tarfile
    #Download update
    update_archive = "/var/tmp/rtkbase_update.tar.gz"
    response = requests.get(update_url)
    with open(update_archive, "wb") as f:
        f.write(response.content)

    #Get the "root" folder in the archive
    tar = tarfile.open(update_archive)
    for tarinfo in tar:
        if tarinfo.isdir():
            primary_folder = tarinfo.name
            break
    
