from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.views.generic.edit import View
from django.db.models import Q
from django.utils import timezone
from oauth2_provider.views import ProtectedResourceView
from datetime import date
from .models import Member
from .templatetags.photo_filter import img2base64
from .mixins import APITokenMixin


@method_decorator(csrf_exempt, name='dispatch')
class ApiV1Smoelenboek(ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        large = request.GET.get('large', '0') == '1'
        members = Member.objects.filter(Q(afmeld_datum__gt=timezone.now()) | Q(afmeld_datum=None))
        day = self.kwargs.get('day', None)
        if day:
            if day == 'vrijdag':
                members = members.filter(dag_vrijdag=True)
            else:
                members = members.filter(dag_zaterdag=True)

        members = members.order_by('first_name')

        response = {'vrijdag': [], 'zaterdag': []}
        for member in members:
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
                "types": ','.join([tmptype.slug for tmptype in member.types.all()]),
                "photo": img2base64(photo)
            }

            if member.dag_vrijdag:
                response['vrijdag'].append(memberdict)
            if member.dag_zaterdag:
                response['zaterdag'].append(memberdict)

        return JsonResponse(data=response)


@method_decorator(csrf_exempt, name='dispatch')
class ApiV1SmoelenboekUser(ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        large = request.GET.get('large', '0') == '1'
        userid = self.kwargs['pk']
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
            "types": ','.join([tmptype.slug for tmptype in member.types.all()]),
            "photo": img2base64(photo)
        }
        return JsonResponse(data=memberdict)


class ApiV1UserDetails(ProtectedResourceView):
    def get(self, request, *args, **kwargs):
        member = request.resource_owner.member
        user_data = {
            "id": str(request.resource_owner.id),
            "firstName": member.first_name,
            "middleName": "",
            "lastName": member.last_name,
            "fullName": member.full_name,
            "username": request.resource_owner.username,
            "email": member.email_address,
            "emailParents": member.email_ouders,
            "dateOfBirth": member.gebdat,
            "address": member.straat,
            "zip": member.postcode,
            "city": member.woonplaats,
            "phone": member.telnr,
            "memberStatus": member.is_active(),
            "accountType": member.idp_types(),
            "backendID": str(member.id)
        }
        return JsonResponse(data=user_data)


@method_decorator(csrf_exempt, name='dispatch')
class ApiV1IDPGetDetails(APITokenMixin, View):

    def post(self, request, *args, **kwargs):

        if not self.check_api_token():
            return HttpResponse(status=403)

        userid = request.POST.get('user-id', '0').strip('u-')
        if not userid:
            return JsonResponse(data={'ok': False, 'error': 'User-id required'}, status=412)
        try:
            member = Member.objects.get(id=userid)
        except Member.DoesNotExist:
            return JsonResponse(data={'ok': False, 'error': 'User not found'}, status=404)

        response = {'user-id': member.id}
        fields = self.kwargs['fields'].split(',')
        for field in fields:
            if field == 'is-member':
                response['is-member'] = member.is_active()
            elif field == 'mail':
                response['mail'] = member.email_address
            elif field == 'mail-parents':
                response['mail-parents'] = member.email_ouders
            elif field == 'city':
                response['city'] = member.woonplaats
            elif field == 'zip':
                response['zip'] = member.postcode
            elif field == 'address':
                response['address'] = member.straat
            elif field == 'phone':
                response['phone'] = member.telnr_ouders
            elif field == 'mobile':
                response['mobile'] = member.telnr
            elif field == 'firstname':
                response['firstname'] = member.first_name
            elif field == 'lastname':
                response['lastname'] = member.last_name
            elif field == 'middlename':
                response['middelname'] = ''
            elif field == 'dob':
                response['dob'] = member.gebdat
            elif field == 'type':
                response['type'] = member.idp_types()

        result = {'ok': True, 'result': response}
        return JsonResponse(data=result)


@method_decorator(csrf_exempt, name='dispatch')
class ApiV1IDPVerify(APITokenMixin, View):

    def post(self, request, *args, **kwargs):
        if not self.check_api_token():
            return HttpResponse(status=403)

        result = Member.objects.filter(Q(afmeld_datum__gt=date.today()) | Q(afmeld_datum=None))

        fields = self.kwargs['fields'].split(',')
        for field in fields:
            value = request.POST.get('email', 'xxxxx').lower()
            if field == 'email':
                result = result.filter(Q(email_address=value) | Q(email_ouders=value))
            elif field == 'zip':
                zipcode = request.POST.get('zip', 'xxxxxx').lower()
                zip_spaced = zipcode[0:4] + ' ' + zipcode[-2:]
                zip_stripped = zipcode.replace(' ', '')
                result = result.filter(Q(postcode=zip_spaced) | Q(postcode=zip_stripped))

        try:
            member = result.get()
        except (Member.DoesNotExist, Member.MultipleObjectsReturned):
            return JsonResponse(data={'ok': True, 'result': None})

        return JsonResponse(data={'ok': True, 'result': 'u-{0}'.format(member.id)})


@method_decorator(csrf_exempt, name='dispatch')
class ApiV1IDPAvatar(APITokenMixin, View):
    def post(self, request, *args, **kwargs):

        if not self.check_api_token():
            return HttpResponse(status=403)

        return JsonResponse(data={'ok': False, 'error': 'Not implemented'}, status=200)
