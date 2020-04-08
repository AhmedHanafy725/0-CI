<template>
  <!-- begin:: Content -->
  <div class="kt-content kt-grid__item kt-grid__item--fluid" id="kt_content">
    <div class="row">
      <div class="col-lg-12">
        <!--begin::Portlet-->
        <div class="kt-portlet">
          <div class="kt-portlet__head">
            <div class="kt-portlet__head-label">
              <h3 class="kt-portlet__head-title">ZeroCI Configuration</h3>
            </div>
          </div>

          <!--begin::Form-->
          <form class="kt-form kt-form--fit kt-form--label-right" @submit.prevent="sendConfig()">
            <div class="kt-portlet__body">
              <div class="form-group row">
                <label class="col-lg-2 col-form-label">Telegram bot token:</label>
                <div class="col-lg-3">
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Enter telegram bot token"
                    v-model="bot_token"
                    required
                  />
                </div>
                <label class="col-lg-2 col-form-label">Telegram chat id:</label>
                <div class="col-lg-3">
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Enter Telegram chat id"
                    v-model="chat_id"
                    required
                  />
                </div>
              </div>
              <div class="form-group row">
                <label class="col-lg-2 col-form-label">VCS (version control system) host:</label>
                <div class="col-lg-3">
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Enter your VCS host"
                    v-model="vcs_host"
                    required
                  />
                </div>
                <label class="col-lg-2 col-form-label">VCS token:</label>
                <div class="col-lg-3">
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Enter your VCS token"
                    v-model="vcs_token"
                    required
                  />
                </div>
              </div>
              <div class="form-group row">
                <label class="col-lg-2 col-form-label">Domain:</label>
                <div class="col-lg-3">
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Enter your Domain"
                    v-model="domain"
                    required
                  />
                </div>
                <label class="col-lg-2 col-form-label">Repo list:</label>
                <div class="col-lg-3">
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Enter your Repo list"
                    v-model="repos"
                    required
                  />
                </div>
              </div>
              <div class="form-group row">
                <label class="col-lg-2 col-form-label">IYO id:</label>
                <div class="col-lg-3">
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Enter your IYO id"
                    v-model="iyo_id"
                    required
                  />
                </div>
                <label class="col-lg-2 col-form-label">IYO secret:</label>
                <div class="col-lg-3">
                  <input
                    type="text"
                    class="form-control"
                    placeholder="Enter your IYO secret"
                    v-model="iyo_secret"
                    required
                  />
                </div>
              </div>
            </div>
            <div class="kt-portlet__foot kt-portlet__foot--fit-x">
              <div class="kt-form__actions">
                <div class="row">
                  <div class="col-lg-2"></div>
                  <div class="col-lg-10">
                    <button type="submit" class="btn btn-success">Submit</button>
                    <button type="reset" class="btn btn-secondary">Cancel</button>
                  </div>
                </div>
              </div>
            </div>
          </form>

          <!--end::Form-->
        </div>

        <!--end::Portlet-->
      </div>
    </div>
  </div>

  <!-- end:: Content -->
</template>

<script>
import EventService from "../services/EventService";
export default {
  name: "InitialConfig",
  data() {
    return {
      bot_token: "",
      chat_id: "",
      vcs_host: "",
      vcs_token: "",
      domain: "",
      repos: "",
      iyo_id: "",
      iyo_secret: ""
    };
  },
  methods: {
    sendConfig() {
      EventService.initial_config(
        this.bot_token,
        this.chat_id,
        this.vcs_host,
        this.vcs_token,
        this.domain,
        this.repos,
        this.iyo_id,
        this.iyo_secret
      )
        .then(response => {
          this.$router.push("/dashboard");
        })
        .catch(error => {
          console.log("Error! Could not reach the API. " + error);
        });
    }
  }
};
</script>
