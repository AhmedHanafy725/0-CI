<template>
  <!-- begin:: Page -->
  <div class="kt-grid kt-grid--ver kt-grid--root">
    <div
      class="kt-grid kt-grid--hor kt-grid--root kt-login kt-login--v4 kt-login--signin"
      id="kt_login"
    >
      <Loading v-if="loading" />
      <div
        class="kt-grid__item kt-grid__item--fluid kt-grid kt-grid--hor"
        style="background-image: url(/static/media/bg/bg-2.jpg);height: 100vh;"
      >
        <div class="kt-grid__item kt-grid__item--fluid kt-login__wrapper">
          <div class="kt-login__container">
            <div class="kt-login__logo">
              <a href="#">
                <img src="/static/media/logos/logo-light.png" />
              </a>
            </div>
            <div class="kt-login__signin">
              <div class="kt-login__head">
                <h3 class="kt-login__title">Configuration</h3>
              </div>
              <form
                class="kt-form kt-form--fit kt-form--label-right"
                @submit.prevent="sendConfig()"
              >
                <div class="kt-portlet__body">
                  <div class="form-group row">
                    <label class="col-lg-4 col-form-label">Telegram bot token:</label>
                    <div class="col-lg-8">
                      <input
                        type="text"
                        class="form-control"
                        placeholder="Enter telegram bot token"
                        v-model="bot_token"
                        required
                      />
                    </div>
                    <label class="col-lg-4 col-form-label">Telegram chat id:</label>
                    <div class="col-lg-8">
                      <input
                        type="text"
                        class="form-control"
                        placeholder="Enter Telegram chat id"
                        v-model="chat_id"
                        required
                      />
                    </div>
                    <label class="col-lg-4 col-form-label">VCS (version control system) host:</label>
                    <div class="col-lg-8">
                      <input
                        type="text"
                        class="form-control"
                        placeholder="Enter your VCS host"
                        v-model="vcs_host"
                        required
                      />
                    </div>
                    <label class="col-lg-4 col-form-label">VCS token:</label>
                    <div class="col-lg-8">
                      <input
                        type="text"
                        class="form-control"
                        placeholder="Enter your VCS token"
                        v-model="vcs_token"
                        required
                      />
                    </div>
                    <label class="col-lg-4 col-form-label">Domain:</label>
                    <div class="col-lg-8">
                      <input
                        type="text"
                        class="form-control"
                        placeholder="Enter your Domain"
                        v-model="domain"
                        required
                      />
                    </div>
                    <label class="col-lg-4 col-form-label">Repo list:</label>
                    <div class="col-lg-8">
                      <textarea
                        class="form-control"
                        id="exampleTextarea"
                        rows="4"
                        placeholder="Enter your Repos seperated by ,"
                        v-model="repos"
                        required
                      ></textarea>
                    </div>
                  </div>
                </div>
                <div class="kt-portlet__foot kt-portlet__foot--fit-x">
                  <div class="kt-login__actions">
                    <button class="btn btn-brand btn-pill kt-login__btn-primary">Apply</button>
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- end:: Page -->

  <!-- end:: Content -->
</template>

<script>
import Loading from "./Loading";
import EventService from "../services/EventService";
export default {
  name: "InitialConfig",
  components: {
    Loading
  },
  data() {
    return {
      loading: true,
      bot_token: "",
      chat_id: "",
      vcs_host: "",
      vcs_token: "",
      domain: "",
      repos: ""
    };
  },
  methods: {
    getConfig() {
      EventService.getConfig()
        .then(response => {
          this.loading = false;
          this.bot_token = response.data.bot_token;
          this.chat_id = response.data.chat_id;
          this.vcs_host = response.data.vcs_host;
          this.vcs_token = response.data.vcs_token;
          this.domain = response.data.domain;
          this.repos = response.data.repos;
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    },
    sendConfig() {
      EventService.initial_config(
        this.bot_token,
        this.chat_id,
        this.vcs_host,
        this.vcs_token,
        this.domain,
        this.repos.split(",")
      ).catch(error => {
        if (error.response.status == 500) {
          this.$router.push("/");
        } else {
          console.log("Error! Could not reach the API. " + error);
        }
      });
    }
  },
  created() {
    this.getConfig();
  }
};
</script>

<style scoped>
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .form-control {
  height: auto !important;
}
.col-form-label {
  color: #fff;
}
.form-group label {
  margin-top: 1rem;
}
.kt-login.kt-login--v4 {
  background-size: cover;
  background-repeat: no-repeat;
}
.kt-login.kt-login--v4 .kt-login__wrapper {
  padding: 6% 2rem 1rem 2rem;
  margin: 0 auto 2rem auto;
  overflow: hidden;
}
.kt-login.kt-login--v4 .kt-login__wrapper .kt-login__container {
  width: 600px;
  margin: 0 auto;
}
.kt-login.kt-login--v4 .kt-login__wrapper .kt-login__container .kt-login__logo {
  text-align: center;
  margin: 0 auto 4rem auto;
}
.kt-login.kt-login--v4 .kt-login__wrapper .kt-login__container .kt-login__head {
  margin-top: 1rem;
  margin-bottom: 3rem;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-login__head
  .kt-login__title {
  text-align: center;
  font-size: 1.5rem;
  font-weight: 500;
  color: #6c7293;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-login__head
  .kt-login__desc {
  margin-top: 1.5rem;
  text-align: center;
  font-size: 1.1rem;
  font-weight: 400;
  color: #a7abc3;
}
.kt-login.kt-login--v4 .kt-login__wrapper .kt-login__container .kt-form {
  margin: 0 auto;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .input-group {
  padding: 0;
  margin: 0 auto;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .form-control {
  height: 46px;
  border: none;
  padding-left: 1.5rem;
  padding-right: 1.5rem;
  /* border-radius: 46px; */
  /* margin-top: 1.5rem; */
  background: rgba(255, 255, 255, 0.015);
  color: #a7abc3;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .form-control::-moz-placeholder {
  color: #6c7293;
  opacity: 1;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .form-control:-ms-input-placeholder {
  color: #6c7293;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .form-control::-webkit-input-placeholder {
  color: #6c7293;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .form-control.is-valid
  + .valid-feedback,
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .form-control.is-invalid
  + .invalid-feedback {
  font-weight: 500;
  font-size: 0.9rem;
  padding-left: 1.6rem;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .kt-login__extra {
  margin-top: 30px;
  margin-bottom: 15px;
  color: #a7abc3;
  font-size: 1rem;
  padding: 0 1.5rem;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .kt-login__extra
  .kt-checkbox {
  font-size: 1rem;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .kt-login__extra
  .kt-login__link {
  font-size: 1rem;
  color: #a7abc3;
  -webkit-transition: color 0.3s ease;
  transition: color 0.3s ease;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .kt-login__extra
  .kt-login__link:hover {
  color: #5d78ff;
  -webkit-transition: color 0.3s ease;
  transition: color 0.3s ease;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .kt-login__actions {
  text-align: center;
  margin-top: 7%;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .kt-login__actions
  .kt-login__btn-secondary,
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-form
  .kt-login__actions
  .kt-login__btn-primary {
  height: 50px;
  padding-left: 2.5rem;
  padding-right: 2.5rem;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-login__account {
  text-align: center;
  margin-top: 2rem;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-login__account
  .kt-login__account-msg {
  font-size: 1rem;
  font-weight: 400;
  color: #a7abc3;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-login__account
  .kt-login__account-link {
  font-size: 1rem;
  font-weight: 500;
  color: #6c7293;
  -webkit-transition: color 0.3s ease;
  transition: color 0.3s ease;
}
.kt-login.kt-login--v4
  .kt-login__wrapper
  .kt-login__container
  .kt-login__account
  .kt-login__account-link:hover {
  color: #5d78ff;
  -webkit-transition: color 0.3s ease;
  transition: color 0.3s ease;
}

.kt-login.kt-login--v4.kt-login--signin .kt-login__signup {
  display: none;
}

.kt-login.kt-login--v4.kt-login--signin .kt-login__signin {
  display: block;
}

.kt-login.kt-login--v4.kt-login--signin .kt-login__forgot {
  display: none;
}

.kt-login.kt-login--v4.kt-login--signup .kt-login__signup {
  display: block;
}

.kt-login.kt-login--v4.kt-login--signup .kt-login__signin {
  display: none;
}

.kt-login.kt-login--v4.kt-login--signup .kt-login__forgot {
  display: none;
}

.kt-login.kt-login--v4.kt-login--signup .kt-login__account {
  display: none;
}

.kt-login.kt-login--v4.kt-login--forgot .kt-login__signup {
  display: none;
}

.kt-login.kt-login--v4.kt-login--forgot .kt-login__signin {
  display: none;
}

.kt-login.kt-login--v4.kt-login--forgot .kt-login__forgot {
  display: block;
}

@media (max-width: 1024px) {
  .kt-login.kt-login--v4 .kt-login__wrapper {
    padding-top: 5rem;
    width: 100%;
  }
  .kt-login.kt-login--v4 .kt-login__wrapper .kt-login__container {
    margin: 0 auto;
  }
  .kt-login.kt-login--v4
    .kt-login__wrapper
    .kt-login__container
    .kt-login__account {
    margin-top: 1rem;
  }
}

@media (max-width: 768px) {
  .kt-login.kt-login--v4 .kt-login__wrapper {
    width: 100%;
  }
  .kt-login.kt-login--v4 .kt-login__wrapper .kt-login__container {
    width: 100%;
    margin: 0 auto;
  }
  .kt-login.kt-login--v4 .kt-login__wrapper .kt-login__container .kt-form {
    width: 100%;
    margin: 0 auto;
  }
  .kt-login.kt-login--v4
    .kt-login__wrapper
    .kt-login__container
    .kt-login__account {
    margin-top: 1rem;
  }
}
</style>
