from flask import request, abort
from flask_classy import route, FlaskView
from flask_login import current_user

from core.web.api.crud import CrudSearchApi
from core.group import Group
from core.web.api.api import render
from core.web.helpers import requires_role, get_object_or_404, requires_permissions
from core.user import User

from mongoengine.errors import InvalidQueryError


class GroupAdmin(FlaskView):
    @route("/", methods=["GET"])
    def index(self):
        if current_user.has_role("admin"):
            groups = Group.objects.all()
        else:
            groups = Group.objects(admins__in=[current_user.id])
        return render(groups)

    @route("/<id>", methods=["GET"])
    def get(self, id):
        group = get_object_or_404(Group, id=id)
        is_admin = current_user.has_role("admin")
        is_group_admin = Group.objects(
            admins__in=[current_user.id], id=id, enabled=True
        )
        if is_admin or is_group_admin:
            return render(group)
        return 403

    @route("/toggle/<id>", methods=["POST"])
    @requires_role("admin")
    def toggle(self, id):
        group = get_object_or_404(Group, id=id)
        group.enabled = not group.enabled
        group.save()
        return render({"enabled": group.enabled, "id": id})

    @route("/<id>", methods=["DELETE"])
    def remove(self, id):
        group = get_object_or_404(Group, id=id)
        group.delete()
        return render({"id": id})

    @route("/add-member", methods=["POST"])
    def add_member(self):
        params = request.get_json(silent=True) or {}
        gid = params.get("gid")
        uid = params.get("uid")
        user = get_object_or_404(User, id=uid)
        group = get_object_or_404(Group, id=gid)
        is_admin = current_user.has_role("admin")
        is_group_admin = current_user in group.admins and group.enabled
        if is_admin or is_group_admin:
            group.update(add_to_set__members=user.id)
            return render(group.reload())
        abort(403)

    @route("/remove-member", methods=["POST"])
    def remove_member(self):
        params = request.get_json(silent=True) or {}
        gid = params.get("gid")
        uid = params.get("uid")
        user = get_object_or_404(User, id=uid)
        group = get_object_or_404(Group, id=gid)
        is_admin = current_user.has_role("admin")
        is_group_admin = current_user in group.admins and group.enabled
        if is_admin or is_group_admin:
            group.update(pull__members=user.id)
            return render(group.reload())
        abort(403)

    @route("/toggle-admin", methods=["POST"])
    def toggle_admin(self):
        params = request.get_json(silent=True) or {}
        gid = params.get("gid")
        uid = params.get("uid")
        user = get_object_or_404(User, id=uid)
        group = get_object_or_404(Group, id=gid)
        is_admin = current_user.has_role("admin")
        is_group_admin = current_user in group.admins and group.enabled
        if is_admin or is_group_admin:
            if user in group.admins:
                group.update(pull__admins=user.id)
            else:
                group.update(add_to_set__admins=user.id)
            return render(group)
        abort(403)


class GroupAdminSearch(CrudSearchApi):
    template = "group_api.html"
    objectmanager = Group

    @requires_permissions("read")
    def post(self):
        """Launches a simple search against the database

        This endpoint is mostly used by paginators in Yeti.

        :<json object params: JSON object specifying the ``page``, ``range`` and ``regex`` variables.
        :<json integer params.page: Page or results to return (default: 1)
        :<json integer params.range: How many results to return (default: 50)
        :<json boolean params.regex: Set to true if the arrays in ``filter`` are to be treated as regular expressions (default: false)
        :<json object filter: JSON object specifying keys to be matched in the database. Each key must contain an array of OR-matched values.

        :reqheader Accept: must be set to ``application/json``
        :reqheader Content-Type: must be set to ``application/json``
        """
        query = request.get_json(silent=True) or {}
        if not current_user.has_role("admin"):
            query.setdefault("filter", {})["admins__in"] = [current_user.id]
            query["filter"]["enabled"] = True

        try:
            data = self.search(query)
        except InvalidQueryError as e:
            logging.error(e)
            abort(400)
        # TODO: frontend-deprecation
        # Remove template rendering here
        return render(data, template=self.template)
