# from django.http import JsonResponse, HttpResponseRedirect
# import paypalrestsdk
# from django.urls import reverse
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
# from rest_framework.decorators import api_view

# @swagger_auto_schema(method='get', responses={200: 'Payment Created!'})
# @api_view(['GET'])
# @swagger_auto_schema(
#     method='get',
#     responses= {
#     200: openapi.Response('Payment Created!'),
#     500: openapi.Response('Error occurred while creating payment.')
# },
# )
# def create_payment(request):
#     amount_to_pay = "10.00"  # Example: Payment of $10.00

#     # Create a payment object
#     payment = paypalrestsdk.Payment({
#         "intent": "sale",
#         "payer": {
#             "payment_method": "paypal"
#         },
#         "redirect_urls": {
#             "return_url": request.build_absolute_uri(reverse('payment_success')),
#             "cancel_url": request.build_absolute_uri(reverse('payment_cancel'))
#         },
#         "transactions": [{
#             "item_list": {
#                 "items": [{
#                     "name": "Item Name",
#                     "sku": "item",
#                     "price": amount_to_pay,
#                     "currency": "USD",
#                     "quantity": 1
#                 }]
#             },
#             "amount": {
#                 "total": amount_to_pay,
#                 "currency": "USD"
#             },
#             "description": "Payment for services"
#         }]
#     })

#     # Execute the payment
#     if payment.create():
#         for link in payment.links:
#             if link.rel == "approval_url":
#                 return HttpResponseRedirect(link.href)
#     else:
#         return JsonResponse({'error': payment.error}, status=500)

# @swagger_auto_schema(method='get', responses={200: 'Payment Created!'})
# @api_view(['GET'])
# @swagger_auto_schema(
#     method='get',
#     responses= {
#     200: openapi.Response('Payment Success!'),
#     500: openapi.Response('Error occurred during payment execution.')
# },
# )
# def payment_success(request):
#     payment_id = request.GET.get('paymentId')
#     payer_id = request.GET.get('PayerID')

#     payment = paypalrestsdk.Payment.find(payment_id)

#     if payment.execute({"payer_id": payer_id}):
#         return JsonResponse({'status': 'Payment completed successfully!'})
#     else:
#         return JsonResponse({'error': payment.error}, status=500)

# @swagger_auto_schema(method='get', responses={200: 'Payment Created!'})
# @api_view(['GET'])
# @swagger_auto_schema(
#     method='get',
#     responses= {
#     200: openapi.Response('Payment cancelled by the user.')
# },
# )
# def payment_cancel(request):
#     return JsonResponse({'status': 'Payment cancelled by the user.'})
