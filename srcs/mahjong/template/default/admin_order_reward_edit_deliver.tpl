<div class="cl-mcont">
    <div class='block'>
         <div class='header'>
             <h3>
             %if info.get('title',None):
               {{info['title']}}
             %end
           </h3>
         </div>

<div class='content'>
      <form class='form-horizontal group-border-dashed' action="{{info['submitUrl']}}" method='POST' id='selfModify'>
       <div class="form-group">
            <label class="col-sm-5 control-label">玩家id</label>
            <div class="col-sm-6">
                  <input type='text' style='width:100%;float:left' name='uid' class="form-control" value='{{uid}}' readonly='readonly'>
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">玩家昵称</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='nickname'  data-rules="{required:true}" class="form-control" value='{{nickname}}' readonly='readonly'>
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">兑换码</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='key_code'  data-rules="{required:true}" class="form-control" value='{{key_code}}' readonly='readonly'>
            </div>
       </div>


       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">卡号</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='card_no'  data-rules="{required:true}" class="form-control" value='{{card_no}}' >
            </div>
       </div>

       <div class="form-group">
            <label class="col-sm-5 col-xs-10 control-label">卡密</label>
            <div class="col-sm-6 col-xs-12">
                  <input type='text' style='width:100%;float:left' name='card_pwd'  data-rules="{required:true}" class="form-control" value='{{card_pwd}}'>
            </div>
       </div>

       <div class="modal-footer" style="text-align:center">
           <button type="submit" class="btn btn-sm btn-xs btn-primary btn-mobile">确认</button>
       </div>


</form>
</div>
</div>
</div>
%rebase admin_frame_base

<script>
    if("{{post_res}}"=="1"){
        alert("发货成功！")
    }else if("{{post_res}}"=="2"){
        alert("发货失败！")
    }else if("{{post_res}}"=="3"){
    }
</script>