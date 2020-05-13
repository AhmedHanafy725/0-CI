<template>
  <div class="kt-grid__item kt-grid__item--fluid kt-grid kt-grid--hor kt-wrapper" id="kt_wrapper">
    <Header-Sec />
    <div class="kt-grid__item kt-grid__item--fluid kt-grid kt-grid--hor">
      <Content-Head />
      <Content-Body />
      <Footer-Sec />
    </div>
  </div>
</template>

<script>
import Header from "./Header";
import ContentHead from "./ContentHead";
import Content from "./Content";
import Footer from "./Footer";
export default {
  name: "ContentWrapper",
  components: {
    "Header-Sec": Header,
    "Content-Head": ContentHead,
    "Content-Body": Content,
    "Footer-Sec": Footer
  }
};
</script>
