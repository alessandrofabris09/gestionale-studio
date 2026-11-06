def layout_email_base(titolo, sottotitolo, contenuto_html, testo_pulsante=None, url_pulsante=None):
    """
    Layout HTML professionale per le email del gestionale.
    """

    pulsante_html = ""

    if testo_pulsante and url_pulsante:
        pulsante_html = f"""
        <div style="margin-top:28px;">
            <a href="{url_pulsante}"
               style="
                    display:inline-block;
                    background:#111827;
                    color:#ffffff;
                    text-decoration:none;
                    padding:14px 22px;
                    border-radius:10px;
                    font-weight:bold;
                    font-size:15px;
               ">
                {testo_pulsante}
            </a>
        </div>
        """

    return f"""
    <div style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif;color:#111827;">

        <div style="max-width:760px;margin:0 auto;padding:32px 18px;">

            <div style="
                background:#111827;
                color:white;
                padding:28px 32px;
                border-radius:18px 18px 0 0;
            ">
                <div style="font-size:13px;letter-spacing:0.08em;text-transform:uppercase;color:#cbd5e1;font-weight:bold;">
                    Studio Tecnico Cloud
                </div>

                <h1 style="margin:8px 0 0 0;font-size:28px;line-height:1.25;">
                    {titolo}
                </h1>

                <p style="margin:10px 0 0 0;color:#d1d5db;font-size:15px;line-height:1.5;">
                    {sottotitolo}
                </p>
            </div>

            <div style="
                background:#ffffff;
                padding:32px;
                border-radius:0 0 18px 18px;
                box-shadow:0 10px 28px rgba(0,0,0,0.08);
            ">
                {contenuto_html}

                {pulsante_html}

                <div style="
                    margin-top:34px;
                    padding-top:20px;
                    border-top:1px solid #e5e7eb;
                    color:#6b7280;
                    font-size:13px;
                    line-height:1.5;
                ">
                    Email generata automaticamente da Studio Tecnico Cloud.<br>
                    Non rispondere a questo messaggio.
                </div>
            </div>

        </div>

    </div>
    """


def tabella_email(headers, rows):
    """
    Crea una tabella HTML elegante per email.
    headers = lista intestazioni
    rows = lista di liste
    """

    intestazioni = ""

    for header in headers:
        intestazioni += f"""
        <th style="
            padding:12px;
            text-align:left;
            background:#111827;
            color:#ffffff;
            font-size:13px;
            border-bottom:1px solid #111827;
        ">
            {header}
        </th>
        """

    righe = ""

    for row in rows:
        celle = ""

        for cella in row:
            celle += f"""
            <td style="
                padding:12px;
                border-bottom:1px solid #e5e7eb;
                font-size:14px;
                color:#111827;
                vertical-align:top;
            ">
                {cella}
            </td>
            """

        righe += f"""
        <tr>
            {celle}
        </tr>
        """

    return f"""
    <table style="
        width:100%;
        border-collapse:collapse;
        margin-top:22px;
        border:1px solid #e5e7eb;
        border-radius:12px;
        overflow:hidden;
    ">
        <thead>
            <tr>
                {intestazioni}
            </tr>
        </thead>

        <tbody>
            {righe}
        </tbody>
    </table>
    """