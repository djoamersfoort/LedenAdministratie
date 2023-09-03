from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.utils import timezone
from oauth2_provider.views import ProtectedResourceView, ScopedProtectedResourceView

from LedenAdministratie.models import Member
from LedenAdministratie.templatetags.photo_filter import img2base64
from LedenAdministratie.utils import Utils


class ApiV1Smoelenboek(ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        large = request.GET.get("large", "0") == "1"
        members = Member.objects.filter(Q(afmeld_datum__gt=timezone.now()) | Q(afmeld_datum=None)).order_by("first_name")

        response = []
        for member in members:
            if large:
                photo = member.foto
            else:
                photo = member.thumbnail
                if photo is None:
                    photo = member.foto

            memberdict = {
                "id": member.id,
                "user_id": f"idp-{member.user.pk}",
                "first_name": member.first_name,
                "last_name": member.last_name,
                "types": ",".join([tmptype.slug for tmptype in member.types.all()]),
                "photo": img2base64(photo),
            }
            response.append(memberdict)

        return JsonResponse(data=response, safe=False)


class ApiV1SmoelenboekUser(ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        large = request.GET.get("large", "0") == "1"
        userid = self.kwargs["pk"]
        try:
            member = Member.objects.get(pk=userid)
        except Member.DoesNotExist:
            return HttpResponse(status=404)

        if large:
            photo = member.foto
        else:
            photo = member.thumbnail
            if photo is None:
                photo = member.foto

        memberdict = {
            "id": member.id,
            "first_name": member.first_name,
            "last_name": member.last_name,
            "types": ",".join([tmptype.slug for tmptype in member.types.all()]),
            "photo": img2base64(photo),
        }
        return JsonResponse(data=memberdict)


class ApiV1UserDetails(ScopedProtectedResourceView):
    def get_scopes(self):
        return ["user/basic"]

    def get(self, request, *args, **kwargs):
        token = Utils.get_access_token(request)
        if token is None:
            return HttpResponseForbidden()

        if not request.resource_owner or not hasattr(request.resource_owner, "member"):
            # Access token User does not have a linked Member record -> deny access
            return HttpResponseForbidden()

        member = request.resource_owner.member
        user_data = {}
        if token.allow_scopes(["user/basic"]):
            user_data.update(
                {
                    "id": str(request.resource_owner.id),
                    "username": request.resource_owner.username,
                    "memberStatus": member.is_active(),
                    "accountType": member.idp_types(),
                    "backendID": str(member.id),
                    "days": member.days,
                }
            )
            if stripcard := member.active_stripcard:
                user_data.update({
                    "stripcard_count": stripcard.count,
                    "stripcard_used": stripcard.used
                })
        if token.allow_scopes(["user/email"]):
            user_data.update({"email": member.email_address})
        if token.allow_scopes(["user/email-parents"]):
            user_data.update({"emailParents": member.email_ouders})
        if token.allow_scopes(["user/names"]):
            user_data.update(
                {
                    "fullName": member.full_name,
                    "firstName": member.first_name,
                    "middleName": "",
                    "lastName": member.last_name,
                }
            )
        if token.allow_scopes(["user/date-of-birth"]):
            user_data.update({"dateOfBirth": member.gebdat})
            user_data.update({"age": member.age})
        if token.allow_scopes(["user/address"]):
            user_data.update(
                {
                    "address": member.straat,
                    "zip": member.postcode,
                    "city": member.woonplaats,
                }
            )
        if token.allow_scopes(["user/telephone"]):
            user_data.update({"phone": member.telnr})
        return JsonResponse(data=user_data)
