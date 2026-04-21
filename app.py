from posit import connect
from shiny import reactive, render
from shiny.express import input, session, ui


ui.page_opts(title="OAuth Credential Diagnostic", fillable=False)


@reactive.calc
def session_token():
    return session.http_conn.headers.get("Posit-Connect-User-Session-Token")


@reactive.calc
def connect_client():
    return connect.Client()


@reactive.calc
def current_content():
    return connect_client().content.get()


@reactive.calc
def associations():
    try:
        return list(current_content().oauth.associations.find())
    except Exception as e:
        return e


with ui.card():
    ui.card_header("Status")

    @render.ui
    def status_display():
        token = session_token()
        items = [ui.tags.li(f"Session token present: {bool(token)}")]
        if token:
            items.append(ui.tags.li(f"Token prefix: {token[:20]}..."))
        try:
            c = current_content()
            items.append(ui.tags.li(f"Content GUID: {c.get('guid')}"))
            items.append(ui.tags.li(f"Content title: {c.get('title')}"))
        except Exception as e:
            items.append(ui.tags.li(f"Content lookup error: {type(e).__name__}: {e}"))
        return ui.tags.ul(*items)


with ui.card():
    ui.card_header("Associated integrations on this content")

    @render.ui
    def integrations_display():
        assocs = associations()
        if isinstance(assocs, Exception):
            return ui.div(
                ui.tags.strong(f"Error ({type(assocs).__name__})"),
                ui.tags.pre(str(assocs)),
                class_="alert alert-danger",
            )
        if not assocs:
            return ui.div(
                "No integrations associated with this content.",
                class_="alert alert-warning",
            )
        rows = []
        for a in assocs:
            guid = a.get("oauth_integration_guid")
            name = a.get("oauth_integration_name")
            type_ = a.get("oauth_integration_type")
            rows.append(ui.tags.li(f"{name} — type={type_} — guid={guid}"))
        return ui.tags.ul(*rows)


with ui.card():
    ui.card_header("Scenario A: get_credentials(token) — no audience")
    ui.markdown(
        "Tests what happens when audience is omitted. Use this for scenarios 1, 4, 5 "
        "(one integration, multiple integrations, no integration)."
    )
    ui.input_action_button("call_no_audience", "Call without audience", class_="btn-primary")

    @render.ui
    def no_audience_result():
        if input.call_no_audience() == 0:
            return ui.div("Not yet called.", class_="text-muted")
        token = session_token()
        if not token:
            return ui.div("No session token available.", class_="alert alert-warning")
        try:
            creds = connect_client().oauth.get_credentials(token)
            return ui.div(
                ui.tags.strong("SUCCESS"),
                ui.tags.pre(f"keys: {list(creds.keys())}"),
                ui.tags.pre(
                    f"access_token (first 40 chars): "
                    f"{str(creds.get('access_token', ''))[:40]}..."
                ),
                class_="alert alert-success",
            )
        except Exception as e:
            return ui.div(
                ui.tags.strong(f"ERROR ({type(e).__name__})"),
                ui.tags.pre(str(e)),
                class_="alert alert-danger",
            )


with ui.card():
    ui.card_header("Scenario B: get_credentials(token, audience=...)")
    ui.markdown(
        "Tests audience resolution. Paste an integration GUID — either one listed above "
        "(scenario 2) or one from a different content item (scenario 3)."
    )
    ui.input_text(
        "audience_input",
        "Audience (integration GUID)",
        placeholder="019d4b6b-1e6f-a700-72c4-39c89a9f6a77",
        width="100%",
    )
    ui.input_action_button("call_with_audience", "Call with audience", class_="btn-primary")

    @render.ui
    def with_audience_result():
        if input.call_with_audience() == 0:
            return ui.div("Not yet called.", class_="text-muted")
        token = session_token()
        if not token:
            return ui.div("No session token available.", class_="alert alert-warning")
        audience = input.audience_input().strip()
        if not audience:
            return ui.div("Enter an audience GUID.", class_="alert alert-warning")
        try:
            creds = connect_client().oauth.get_credentials(token, audience=audience)
            return ui.div(
                ui.tags.strong("SUCCESS"),
                ui.tags.pre(f"audience: {audience}"),
                ui.tags.pre(f"keys: {list(creds.keys())}"),
                ui.tags.pre(
                    f"access_token (first 40 chars): "
                    f"{str(creds.get('access_token', ''))[:40]}..."
                ),
                class_="alert alert-success",
            )
        except Exception as e:
            return ui.div(
                ui.tags.strong(f"ERROR ({type(e).__name__})"),
                ui.tags.pre(f"audience: {audience}"),
                ui.tags.pre(str(e)),
                class_="alert alert-danger",
            )
