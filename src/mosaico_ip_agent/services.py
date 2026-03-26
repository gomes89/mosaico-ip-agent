#  Copyright (c) 2026 André S. Gomes
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of
#  this software and associated documentation files (the "Software"), to deal in
#  the Software without restriction, including without limitation the rights to
#  use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
#  the Software, and to permit persons to whom the Software is furnished to do so,
#  subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
#  FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
#  COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
#  IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
#  CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
#  SPDX-License-Identifier: MIT

"""
External API services for the MOSAICO IP Agent.

This module provides asynchronous functions to query third-party services
(Eclipse Foundation and ClearlyDefined) for software package license information.
"""

import httpx


async def query_eclipse_foundation(p_type: str, provider: str, namespace: str, name: str, version: str):
    """
    Queries the Eclipse Foundation GitLab repository for license curation data.

    Constructs a specific path based on the package details to fetch the `info.json`
    file from the Eclipse Foundation's IPLab curations repository. It requires a
    specific version to perform the lookup; without one, the request is safely aborted.

    Args:
        p_type (str): The package type/ecosystem (e.g., 'npm', 'pypi', 'maven').
        provider (str): provider (str): The upstream registry or source hosting the package
            (e.g., 'npmjs', 'pypi', 'mavencentral', 'github').
        namespace (str): The organization, group, or user scope (e.g., '@babel' for npm or 'org.apache' for Maven);
            use '-' if no namespace exists.
        name (str): The exact name of the software package.
        version (str): The specific version of the package.


    Returns:
        dict | None: A dictionary containing the 'license' string and the 'source' name
        if the request succeeds. Returns None if the version is invalid, the request fails,
        or the curation data does not exist.
    """
    if not version or version == "-" or version.lower() == "latest":
        return None
    ef_id = f"{p_type.lower()}/{provider}/{namespace}/{name}/{version}"
    url = f"https://gitlab.eclipse.org/eclipsefdn/emo-team/iplab/-/raw/master/curations/{ef_id}/info.json"
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return {"license": data.get("license", "Unknown"), "source": "Eclipse Foundation"}
    except Exception:
        pass
    return None


async def query_clearly_defined(p_type: str, provider: str, namespace: str, name: str, version: str):
    """
    Queries the ClearlyDefined API for package license definitions.

    Calls the public ClearlyDefined definitions endpoint to retrieve the declared license
    for a given package. This function includes an automatic retry mechanism (up to 2 attempts)
    to handle transient network instability or timeouts.

    Args:
        p_type (str): The package type/ecosystem (e.g., 'npm', 'pypi', 'maven').
        provider (str): provider (str): The upstream registry or source hosting the package
            (e.g., 'npmjs', 'pypi', 'mavencentral', 'github').
        namespace (str): The organization, group, or user scope (e.g., '@babel' for npm or 'org.apache' for Maven);
            use '-' if no namespace exists.
        name (str): The exact name of the software package.
        version (str): The specific version of the package. If missing, '-', or 'latest',
            the URL adapts to query general package data without a strict version constraint.

    Returns:
        dict | None: A dictionary containing the 'license' string and the 'source' name
        if the request succeeds. Returns None if all retries fail, the endpoint times out,
        or the package definition is not found.
    """
    headers = {"Accept": "application/json", "Accept-Version": "1.0.0"}
    url = f"https://api.clearlydefined.io/definitions/{p_type}/{provider}/{namespace}/{name}"
    if version and version != "-" and version.lower() != "latest":
        url += f"/{version}"

    async with httpx.AsyncClient() as client:
        for attempt in range(2):
            try:
                r = await client.get(url, headers=headers, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    lic = data.get("licensed", {}).get("declared", "Unknown")
                    return {"license": lic, "source": "ClearlyDefined"}
            except Exception:
                if attempt == 0:
                    continue
    return None
