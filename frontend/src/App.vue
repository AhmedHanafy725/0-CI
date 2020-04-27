<template>
  <v-app>
    <v-content>
      <router-view />
    </v-content>
  </v-app>
</template>

<script>
export default {
  name: "App",
   mounted: function() {
    let elHtml = document.getElementsByTagName('html')[0]
    elHtml.style.overflowY = 'auto'
  },
  destroyed: function() {
    let elHtml = document.getElementsByTagName('html')[0]
    elHtml.style.overflowY = null
  }
};
</script>

<style src="./assets/perfect-scrollbar/css/perfect-scrollbar.css"></style>
<style src="../static/vendors/general/tether/dist/css/tether.css"></style>
<style src="../static/vendors/general/bootstrap-datepicker/dist/css/bootstrap-datepicker3.css"></style>
<style src="../static/vendors/general/bootstrap-datetime-picker/css/bootstrap-datetimepicker.css"></style>
<style src="../static/vendors/general/bootstrap-timepicker/css/bootstrap-timepicker.css"></style>
<style src="../static/vendors/general/bootstrap-daterangepicker/daterangepicker.css"></style>
<style src="../static/vendors/general/bootstrap-touchspin/dist/jquery.bootstrap-touchspin.css"></style>
<style src="../static/vendors/general/bootstrap-select/dist/css/bootstrap-select.css"></style>
<style src="../static/vendors/general/bootstrap-switch/dist/css/bootstrap3/bootstrap-switch.css"></style>
<style src="../static/vendors/general/select2/dist/css/select2.css"></style>
<style src="../static/vendors/general/ion-rangeslider/css/ion.rangeSlider.css"></style>
<style src="../static/vendors/general/nouislider/distribute/nouislider.css"></style>
<style src="../static/vendors/general/owl.carousel/dist/assets/owl.carousel.css"></style>
<style src="../static/vendors/general/owl.carousel/dist/assets/owl.theme.default.css"></style>
<style src="../static/vendors/general/dropzone/dist/dropzone.css"></style>
<style src="../static/vendors/general/summernote/dist/summernote.css"></style>
<style src="../static/vendors/general/bootstrap-markdown/css/bootstrap-markdown.min.css"></style>
<style src="../static/vendors/general/animate.css/animate.css"></style>
<style src="../static/vendors/general/toastr/build/toastr.css"></style>
<style src="../static/vendors/general/morris.js/morris.css"></style>
<style src="../static/vendors/general/sweetalert2/dist/sweetalert2.css"></style>
<style src="./assets/socicon/css/socicon.css"></style>
<style src="./assets/line-awesome/css/line-awesome.css"></style>
<style src="./assets/flaticon/flaticon.css"></style>
<style src="./assets/flaticon2/flaticon.css"></style>
<style src="./assets/fontawesome5/css/all.min.css"></style>

<style src="./assets/css/style.bundle.css"></style>
<style src="./assets/css/light.css"></style>
<style src="./assets/css/dark.css"></style>
<style src="./assets/css/aside-dark.css"></style>
<style src="./assets/css/custom.css"></style>


